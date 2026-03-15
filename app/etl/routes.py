"""Rutas del blueprint ETL"""
import os
import pandas as pd
from datetime import date, datetime
from uuid import uuid4
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import json
from sqlalchemy import text
from app.models import db, ETLProjectLog, Users, _ahora_bogota
from app.etl.processors import DataProcessor
from . import etl_bp


def _registrar_progreso(payload, etapa, estado, mensaje):
    """
    Registra hitos confirmados por backend para que frontend no simule etapas.

    Nota: Flask en este flujo responde de forma sincrona al final de la
    peticion. Por ello, el frontend solo muestra etapas que el servidor reporta
    como iniciadas/finalizadas en el payload final.
    """
    payload.setdefault('progreso', []).append({
        'etapa': etapa,
        'estado': estado,
        'mensaje': mensaje,
    })
    payload['estado_validacion'] = {
        'etapa': etapa,
        'estado': estado,
        'mensaje': mensaje,
    }


def _normalizar_serie_numerica(serie):
    """Normaliza texto numérico para mejorar conversión robusta en ETL."""
    def _normalizar_valor(valor):
        if pd.isna(valor):
            return valor

        texto = str(valor).strip().replace(' ', '')
        if texto == '':
            return texto

        # Soporta notación mixta: 1.234,56 (ES) y 1,234.56 (EN).
        if '.' in texto and ',' in texto:
            if texto.rfind(',') > texto.rfind('.'):
                return texto.replace('.', '').replace(',', '.')
            return texto.replace(',', '')

        # Si solo hay coma, intenta distinguir decimal de miles.
        if ',' in texto:
            partes = texto.split(',')
            if len(partes) == 2 and len(partes[1]) <= 2:
                return texto.replace(',', '.')
            return texto.replace(',', '')

        return texto

    return serie.apply(_normalizar_valor)


def _validar_y_transformar_columnas_numericas(df, columnas_objetivo):
    """
    Valida columnas numéricas con coerción estricta y retorna filas corruptas.

    METODOLOGÍA (TESIS):
    Este bloque garantiza calidad del dato en fase de Transformación antes de
    persistencia, detectando "basura" (texto/celdas corruptas) por fila exacta.
    """
    errores_detalle = []

    for etiqueta, col_real in columnas_objetivo.items():
        if col_real not in df.columns:
            continue

        original = df[col_real]
        original_str = original.astype(str).str.strip()
        normalizada = _normalizar_serie_numerica(original)
        convertida = pd.to_numeric(normalizada, errors='coerce')

        # "Basura": valor informado pero no convertible a número.
        mask_basura = convertida.isna() & original.notna() & (original_str != '')
        filas_con_basura = (df.index[mask_basura] + 2).tolist()

        if filas_con_basura:
            errores_detalle.append({
                'columna': etiqueta,
                'filas': filas_con_basura
            })

        # Normalización de tipos según modelo destino en BD.
        if etiqueta in ['despachada', 'devuelta', 'vendida', 'sorteo']:
            df[col_real] = convertida.round().astype('Int64')
        else:
            # Columnas monetarias DECIMAL: mantener precisión con redondeo estable.
            df[col_real] = convertida.round(2)

    return errores_detalle


def _mapear_columnas(df):
    """
    Mapea columnas del archivo a nombres estandar del proceso ETL.

    Retorna una tupla (columnas_mapeadas, normalizaciones) donde
    'normalizaciones' es una lista técnica de normalizaciones aplicadas.
    La comparación es insensible a mayúsculas/minúsculas y espacios
    adicionales porque df.columns ya fue normalizado antes de esta llamada.
    """
    columnas_esperadas = {
        'anio': ['anio', 'año', 'year'],
        'mes': ['mes', 'month'],
        'dia': ['dia', 'día', 'day'],
        'sorteo': ['sorteo', 'numero sorteo', 'num sorteo'],
        'distribuidor': ['distribuidor', 'codigo distribuidor', 'cod distribuidor', 'codigo_distribuidor'],
        'despachada': [
            'despachada', 'cantidad despachada', 'cant despachada',
            'fracciones despachadas', 'cant. despacho',
        ],
        'devuelta': [
            'devuelta', 'cantidad devuelta', 'cant devuelta',
            'fracciones devueltas', 'cant. devolución',
        ],
        'vendida': [
            'vendida', 'cantidad vendida', 'cant vendida',
            'fracciones vendidas', 'cant. venta',
        ],
        'bruto_despacho': ['bruto despacho', 'bruto despachado', 'bruto_despacho'],
        'bruto_devuelto': ['bruto devuelto', 'bruto_devuelto'],
        'bruto_vendido': ['bruto vendido', 'brutovendido', 'bruto'],
        'neto_vendido': ['neto vendido', 'netovendido', 'neto'],
        'porcentaje': ['porcentaje', 'porcentaje comision', 'porcentaje_comision', '% comision'],
    }

    columnas_mapeadas = {}
    normalizaciones = []
    for col_estandar, variantes in columnas_esperadas.items():
        for variante in variantes:
            if variante in df.columns:
                columnas_mapeadas[col_estandar] = variante
                # Si el sinónimo encontrado difiere del nombre estándar,
                # registrar normalización solo para trazabilidad técnica interna.
                if variante != col_estandar:
                    normalizaciones.append(
                        f"Columna '{variante}' reconocida y normalizada como '{col_estandar}'"
                    )
                break
    return columnas_mapeadas, normalizaciones


def validar_formato(df):
    """
    ETAPA 1: VALIDACION DE FORMATO.

    Esta etapa valida estructura del archivo (columnas requeridas) y tipos
    de dato numéricos. Si no se supera, el registro se considera bloqueante
    porque no existe base confiable para persistir en BD.
    """
    errores_criticos = []
    advertencias = []

    # Normalizar encabezados para permitir matching robusto.
    df.columns = df.columns.str.strip().str.lower()
    columnas_mapeadas, _normalizaciones_alias = _mapear_columnas(df)

    # Si porcentaje no viene en archivo, se completa por regla operativa.
    if 'porcentaje' not in columnas_mapeadas:
        df['porcentaje'] = 25.0
        columnas_mapeadas['porcentaje'] = 'porcentaje'
        advertencias.append(
            'Columna "Porcentaje" no encontrada; se asigno 25.0 por defecto a todos los registros.'
        )

    columnas_criticas = [
        'anio', 'mes', 'dia', 'sorteo', 'distribuidor',
        'despachada', 'devuelta', 'vendida',
        'bruto_despacho', 'bruto_devuelto', 'bruto_vendido',
        'neto_vendido',
    ]

    columnas_faltantes = [col for col in columnas_criticas if col not in columnas_mapeadas]
    if columnas_faltantes:
        errores_criticos.append(
            'Faltan columnas criticas en el archivo: ' + ', '.join(columnas_faltantes)
        )
        return {
            'df': df,
            'columnas_mapeadas': columnas_mapeadas,
            'errores_criticos': errores_criticos,
            'advertencias': advertencias
        }

    # Avisar nulos en columnas clave para que el usuario revise origen.
    for col_estandar in columnas_criticas:
        col_real = columnas_mapeadas[col_estandar]
        nulos_count = int(df[col_real].isna().sum())
        if nulos_count > 0:
            advertencias.append(f'{col_estandar.capitalize()}: {nulos_count} valores nulos detectados')

    # Endurecer tipos numéricos para detectar basura por celda/fila.
    columnas_numericas_objetivo = {
        'anio': columnas_mapeadas.get('anio'),
        'mes': columnas_mapeadas.get('mes'),
        'dia': columnas_mapeadas.get('dia'),
        'sorteo': columnas_mapeadas.get('sorteo'),
        'despachada': columnas_mapeadas.get('despachada'),
        'devuelta': columnas_mapeadas.get('devuelta'),
        'vendida': columnas_mapeadas.get('vendida'),
        'bruto_despacho': columnas_mapeadas.get('bruto_despacho'),
        'bruto_devuelto': columnas_mapeadas.get('bruto_devuelto'),
        'bruto_vendido': columnas_mapeadas.get('bruto_vendido'),
        'neto_vendido': columnas_mapeadas.get('neto_vendido'),
        'porcentaje': columnas_mapeadas.get('porcentaje')
    }

    errores_formato_numerico = _validar_y_transformar_columnas_numericas(
        df,
        columnas_numericas_objetivo
    )

    if errores_formato_numerico:
        errores_criticos.append(
            'Se encontraron valores no numericos en columnas requeridas para carga.'
        )
        for detalle in errores_formato_numerico:
            filas = ', '.join(str(f) for f in detalle.get('filas', [])[:20])
            errores_criticos.append(
                f"Columna {detalle.get('columna')}: filas con formato invalido -> {filas}"
            )

    # Porcentaje nulo se completa para permitir auditoría contable.
    col_porcentaje = columnas_mapeadas.get('porcentaje')
    if col_porcentaje:
        filas_porcentaje_nulo = (df.index[df[col_porcentaje].isna()] + 2).tolist()
        if filas_porcentaje_nulo:
            df[col_porcentaje] = df[col_porcentaje].fillna(25.0)
            advertencias.append(
                'Se asigno Porcentaje = 25.0 en filas con nulo: '
                + ', '.join(str(f) for f in filas_porcentaje_nulo[:20])
            )

    return {
        'df': df,
        'columnas_mapeadas': columnas_mapeadas,
        'errores_criticos': errores_criticos,
        'advertencias': advertencias
    }


def validar_integridad(df, columnas_mapeadas):
    """
    ETAPA 2: VALIDACION DE INTEGRIDAD.

    Errores criticos bloqueantes definidos para este flujo:
    - Sorteo repetido
    - Codigos de distribuidor no registrados

    Tambien se valida fecha parseable como guardarraíl de consistencia.
    """
    errores_criticos = []

    # Control de duplicidad de sorteos (integridad por lote).
    col_sorteo = columnas_mapeadas['sorteo']
    sorteos_archivo = [int(v) for v in df[col_sorteo].dropna().unique().tolist()]
    if sorteos_archivo:
        from app.models import FactVentas
        sorteo_existente = FactVentas.query.filter(FactVentas.sorteo.in_(sorteos_archivo)).first()
        if sorteo_existente:
            errores_criticos.append(f'El sorteo {sorteo_existente.sorteo} ya ha sido cargado previamente.')

    # Control de maestro de distribuidores.
    from app.models import DimDistribuidor
    col_distribuidor = columnas_mapeadas['distribuidor']
    codigos_archivo = df[col_distribuidor].dropna().astype(str).str.strip().unique().tolist()
    distribuidores_bd = DimDistribuidor.query.filter(
        DimDistribuidor.codigo_distribuidor.in_(codigos_archivo)
    ).all()
    codigos_bd = {dist.codigo_distribuidor for dist in distribuidores_bd}
    codigos_faltantes = [cod for cod in codigos_archivo if cod not in codigos_bd]
    if codigos_faltantes:
        errores_criticos.append(
            'Codigos de distribuidor no existentes: ' + ', '.join(codigos_faltantes)
        )

    # Control de integridad temporal de entrada.
    col_anio = columnas_mapeadas['anio']
    col_mes = columnas_mapeadas['mes']
    col_dia = columnas_mapeadas['dia']
    errores_tiempo = []
    for idx, row in df.iterrows():
        try:
            date(int(row[col_anio]), int(row[col_mes]), int(row[col_dia]))
        except Exception:
            errores_tiempo.append(idx + 2)
    if errores_tiempo:
        errores_criticos.append(
            'Hay fechas invalidas en columnas Anio/Mes/Dia. '
            + f'Filas: {", ".join(str(f) for f in errores_tiempo[:20])}'
        )

    return errores_criticos


def validar_reglas_negocio(df, columnas_mapeadas):
    """
    ETAPA 3: REGLAS DE NEGOCIO CONTABLES.

    Fórmulas auditadas por fila:
    1) Despachada - Devuelta == Vendida
    2) Bruto despacho - Bruto devuelto == Bruto vendido
    3) Neto vendido == (Bruto vendido * (100 - Porcentaje) / 100)

    Estas inconsistencias se reportan como advertencias (no bloqueantes)
    para mantener trazabilidad de calidad de dato sin frenar la carga.
    """
    advertencias = []
    tolerancia = 0.01

    for idx, row in df.iterrows():
        # UX: el usuario final cuenta datos desde la primera fila de contenido,
        # no incluye la fila de encabezado del archivo.
        fila_usuario = idx + 1

        despachada = float(row[columnas_mapeadas['despachada']])
        devuelta = float(row[columnas_mapeadas['devuelta']])
        vendida = float(row[columnas_mapeadas['vendida']])
        bruto_despacho = float(row[columnas_mapeadas['bruto_despacho']])
        bruto_devuelto = float(row[columnas_mapeadas['bruto_devuelto']])
        bruto_vendido = float(row[columnas_mapeadas['bruto_vendido']])
        neto_vendido = float(row[columnas_mapeadas['neto_vendido']])
        porcentaje = float(row[columnas_mapeadas['porcentaje']])

        if abs((despachada - devuelta) - vendida) > tolerancia:
            advertencias.append(
                f'Fila {fila_usuario}: Inconsistencia en Cantidades (Despachada - Devuelta != Vendida)'
            )

        if abs((bruto_despacho - bruto_devuelto) - bruto_vendido) > tolerancia:
            advertencias.append(
                f'Fila {fila_usuario}: Inconsistencia en Brutos (Bruto despacho - Bruto devuelto != Bruto vendido)'
            )

        neto_calculado = bruto_vendido * (100 - porcentaje) / 100
        if abs(neto_vendido - neto_calculado) > tolerancia:
            advertencias.append(
                f'Fila {fila_usuario}: Inconsistencia en Neto Vendido (Neto vendido != Bruto vendido * (100 - Porcentaje) / 100)'
            )

    return advertencias


def _construir_datos_previsualizados(df):
    """
    Convierte el DataFrame en JSON estructurado para pintar preview.

    Se serializa el DataFrame completo para que el frontend gestione
    la paginacion visual en bloques de 10 filas.
    """
    muestra = df.copy()
    muestra = muestra.where(pd.notna(muestra), None)

    return {
        'total_filas': int(len(df)),
        'filas_mostradas': int(len(muestra)),
        'columnas': [str(c) for c in muestra.columns.tolist()],
        'filas': json.loads(muestra.to_json(orient='records', date_format='iso'))
    }


def _int_or_default(value, default=0):
    """Convierte valores numéricos (incluyendo pandas nullable) a int seguro."""
    if pd.isna(value):
        return default
    return int(value)


def _float_or_default(value, default=0.0):
    """Convierte valores numéricos (incluyendo pandas nullable) a float seguro."""
    if pd.isna(value):
        return default
    return float(value)


def _obtener_o_crear_id_tiempo(fecha):
    """Obtiene o crea registro en Dim_Tiempo y retorna su id_tiempo."""
    row = db.session.execute(
        text('SELECT id_tiempo FROM Dim_Tiempo WHERE fecha = :fecha LIMIT 1'),
        {'fecha': fecha}
    ).first()
    if row:
        return int(row[0])

    dia_semana_num = fecha.isoweekday()
    dia_semana_nombres = {
        1: 'Lunes', 2: 'Martes', 3: 'Miercoles', 4: 'Jueves',
        5: 'Viernes', 6: 'Sabado', 7: 'Domingo'
    }
    dia_semana_nombre = dia_semana_nombres[dia_semana_num]
    es_fin_semana = dia_semana_num in (6, 7)
    trimestre = ((fecha.month - 1) // 3) + 1

    db.session.execute(
        text(
            'INSERT INTO Dim_Tiempo '
            '(fecha, anio, mes, dia, dia_semana_nombre, dia_semana_num, es_fin_semana, trimestre) '
            'VALUES (:fecha, :anio, :mes, :dia, :dia_semana_nombre, :dia_semana_num, :es_fin_semana, :trimestre)'
        ),
        {
            'fecha': fecha,
            'anio': fecha.year,
            'mes': fecha.month,
            'dia': fecha.day,
            'dia_semana_nombre': dia_semana_nombre,
            'dia_semana_num': dia_semana_num,
            'es_fin_semana': es_fin_semana,
            'trimestre': trimestre,
        }
    )

    row_new = db.session.execute(
        text('SELECT id_tiempo FROM Dim_Tiempo WHERE fecha = :fecha LIMIT 1'),
        {'fecha': fecha}
    ).first()
    return int(row_new[0])


def _guardar_df_temporal(df):
    """Guarda dataframe temporal en disco y retorna ruta absoluta."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    temp_dir = os.path.join(base_dir, 'uploads', 'tmp')
    os.makedirs(temp_dir, exist_ok=True)

    filename = f'upload_{uuid4().hex}.json'
    temp_path = os.path.join(temp_dir, filename)
    df.to_json(temp_path, orient='split')
    return temp_path


def _cargar_df_temporal(ruta_df):
    """Carga dataframe temporal desde ruta persistida en sesión."""
    if not ruta_df or not os.path.exists(ruta_df):
        raise FileNotFoundError('Archivo temporal de carga no encontrado.')
    return pd.read_json(ruta_df, orient='split')


def _es_admin_auditoria(user):
    """Valida rol administrativo para operaciones criticas de auditoria."""
    role_name = ''
    if getattr(user, 'role', None) and getattr(user.role, 'name', None):
        role_name = str(user.role.name).strip()
    return role_name in ('Administrador', 'admin')


@etl_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """
    Página principal de carga de archivos con validación por capas.
    
    GET: Mostrar formulario
    POST: Procesar y validar archivo cargado
    
    METODOLOGÍA (TESIS):
    Este endpoint implementa un sistema de validación por capas que garantiza
    la calidad del dato antes de la persistencia. Las capas son:
    1. Validación de Formato (Pandas): Integridad estructural del archivo
    2. Validación de Integridad (SQLAlchemy): Consistencia con datos maestros
    """
    if request.method == 'GET':
        return render_template('etl/upload.html')

    payload = {
        'puede_cargar': False,
        'errores_criticos': [],
        'advertencias': [],
        'progreso': [],
        'estado_validacion': {
            'etapa': 'inicio',
            'estado': 'iniciado',
            'mensaje': 'Solicitud recibida por el servidor.'
        },
        'datos_previsualizados': {
            'total_filas': 0,
            'filas_mostradas': 0,
            'columnas': [],
            'filas': []
        }
    }

    _registrar_progreso(payload, 'recepcion_archivo', 'iniciado', 'Solicitud recibida por el servidor.')

    if 'file' not in request.files:
        payload['errores_criticos'].append('No se selecciono ningun archivo.')
        _registrar_progreso(payload, 'recepcion_archivo', 'error', 'No se selecciono ningun archivo.')
        return jsonify(payload), 200

    file = request.files['file']
    if file.filename == '':
        payload['errores_criticos'].append('No se selecciono ningun archivo.')
        _registrar_progreso(payload, 'recepcion_archivo', 'error', 'No se selecciono ningun archivo.')
        return jsonify(payload), 200

    if not DataProcessor.allowed_file(file.filename):
        payload['errores_criticos'].append('Formato de archivo no permitido. Use CSV o Excel.')
        _registrar_progreso(payload, 'recepcion_archivo', 'error', 'Formato de archivo no permitido.')
        return jsonify(payload), 200

    try:
        from io import BytesIO

        file_bytes = file.read()
        file_stream = BytesIO(file_bytes)

        _registrar_progreso(payload, 'lectura_archivo', 'iniciado', 'Leyendo archivo en servidor...')
        df, error = DataProcessor.read_file(file_stream, filename=file.filename)
        if error:
            payload['errores_criticos'].append(f'Error al leer el archivo: {error}')
            _registrar_progreso(payload, 'lectura_archivo', 'error', 'No fue posible leer el archivo.')
            return jsonify(payload), 200
        _registrar_progreso(payload, 'lectura_archivo', 'finalizado', 'Archivo leido correctamente.')

        # Flujo unificado por etapas: formato -> integridad -> reglas negocio.
        _registrar_progreso(payload, 'validar_formato', 'iniciado', 'Validando formato y tipos de datos...')
        resultado_formato = validar_formato(df)
        df_validado = resultado_formato['df']
        columnas_mapeadas = resultado_formato['columnas_mapeadas']

        payload['errores_criticos'].extend(resultado_formato['errores_criticos'])
        payload['advertencias'].extend(resultado_formato['advertencias'])
        _registrar_progreso(payload, 'validar_formato', 'finalizado', 'Validacion de formato finalizada.')

        if columnas_mapeadas:
            _registrar_progreso(payload, 'validar_integridad', 'iniciado', 'Validando integridad de sorteo y distribuidores...')
            payload['errores_criticos'].extend(validar_integridad(df_validado, columnas_mapeadas))
            _registrar_progreso(payload, 'validar_integridad', 'finalizado', 'Validacion de integridad finalizada.')

            # Las reglas contables son advertencias no bloqueantes.
            _registrar_progreso(payload, 'validar_reglas_negocio', 'iniciado', 'Validando reglas de negocio contables...')
            payload['advertencias'].extend(validar_reglas_negocio(df_validado, columnas_mapeadas))
            _registrar_progreso(payload, 'validar_reglas_negocio', 'finalizado', 'Validacion de reglas de negocio finalizada.')

        payload['datos_previsualizados'] = _construir_datos_previsualizados(df_validado)

        # Persistir solo cuando no existen errores críticos.
        puede_cargar = len(payload['errores_criticos']) == 0
        payload['puede_cargar'] = puede_cargar
        if puede_cargar:
            _registrar_progreso(payload, 'resultado_final', 'finalizado', 'Validacion finalizada sin errores criticos.')
        else:
            _registrar_progreso(payload, 'resultado_final', 'finalizado', 'Validacion finalizada con errores criticos.')

        temp_data_path = _guardar_df_temporal(df_validado)
        session['upload_data'] = {
            'filename': file.filename,
            'data_path': temp_data_path,
            'columnas_mapeadas': columnas_mapeadas,
            'advertencias': payload['advertencias'],
            'validacion_unificada': True,
            'negocio_validado': True,
            'puede_cargar': puede_cargar
        }

        return jsonify(payload), 200
    except Exception as e:
        payload['errores_criticos'].append(f'Error al procesar el archivo: {str(e)}')
        _registrar_progreso(payload, 'resultado_final', 'error', 'Ocurrio un error inesperado durante la validacion.')
        return jsonify(payload), 200


@etl_bp.route('/validate-business', methods=['POST'])
@login_required
def validate_business():
    """Ruta de compatibilidad: reglas de negocio ya incluidas en upload unificado."""
    upload_data = session.get('upload_data')
    if not upload_data or not upload_data.get('validacion_unificada'):
        return jsonify({
            'error': 'No hay una carga validada en sesion. Cargue y valide el archivo nuevamente.',
            'bloquear_guardado': True
        }), 400

    try:
        df = _cargar_df_temporal(upload_data.get('data_path'))
        columnas_mapeadas = upload_data.get('columnas_mapeadas', {})

        advertencias = validar_reglas_negocio(df, columnas_mapeadas)
        upload_data['advertencias'] = advertencias
        upload_data['negocio_validado'] = True
        session['upload_data'] = upload_data
        payload_ok = {
            'message': 'Las reglas de negocio ya se validan en la carga inicial.',
            'advertencias': advertencias,
            'puede_cargar': bool(upload_data.get('puede_cargar'))
        }
        return jsonify(payload_ok), 200
    except Exception as e:
        return jsonify({
            'error': f'Error al consultar reglas de negocio: {str(e)}',
            'bloquear_guardado': True
        }), 400


@etl_bp.route('/confirm-upload', methods=['POST'])
@login_required
def confirm_upload():
    """
    Fase 3 del ETL: persistencia en Fact_Ventas.

    METODOLOGÍA (TESIS):
    Solo persiste si las capas previas fueron aprobadas (formato y negocio),
    ejecutando inserción transaccional para mantener consistencia.

    Diseno de Log Inmutable:
    Cada carga confirmada registra un evento CARGA en etl_project_logs sin
    sobrescribir eventos anteriores, cumpliendo trazabilidad normativa.
    """
    if 'upload_data' not in session:
        return jsonify({'ok': False, 'error': 'Sesión expirada. Intente nuevamente.'}), 400

    # En el flujo unificado, solo se permite persistir si no hubo errores críticos.
    if not session['upload_data'].get('validacion_unificada'):
        return jsonify({'ok': False, 'error': 'Debe ejecutar la validación unificada antes de guardar.'}), 400

    if not session['upload_data'].get('puede_cargar'):
        return jsonify({'ok': False, 'error': 'No se puede guardar: existen errores críticos de validación.'}), 400
    
    try:
        from app.models import DimDistribuidor, FactVentas

        upload_data = session['upload_data']
        df = _cargar_df_temporal(upload_data.get('data_path'))
        columnas_mapeadas = upload_data.get('columnas_mapeadas', {})

        col_distribuidor = columnas_mapeadas['distribuidor']
        col_anio = columnas_mapeadas['anio']
        col_mes = columnas_mapeadas['mes']
        col_dia = columnas_mapeadas['dia']
        codigos_archivo = df[col_distribuidor].dropna().astype(str).str.strip().unique().tolist()
        distribuidores = DimDistribuidor.query.filter(
            DimDistribuidor.codigo_distribuidor.in_(codigos_archivo)
        ).all()
        distribuidores_por_codigo = {d.codigo_distribuidor: d for d in distribuidores}

        # ETAPA 3: TRAZABILIDAD Y PERSISTENCIA TRANSACCIONAL.
        # Cada registro queda etiquetado por lote (nombre_archivo + fecha_carga)
        # para habilitar rollback/eliminación futura por lote de carga.
        registros_a_insertar = []
        fecha_carga_lote = _ahora_bogota()
        nombre_archivo_lote = upload_data.get('filename', 'archivo_sin_nombre')
        for _, row in df.iterrows():
            codigo = str(row[col_distribuidor]).strip()
            distribuidor = distribuidores_por_codigo.get(codigo)

            # Guardarraíl defensivo: si falla mapeo, evita inserción inconsistente.
            if not distribuidor or not distribuidor.id_municipio:
                continue

            fecha_venta = date(
                _int_or_default(row[col_anio]),
                _int_or_default(row[col_mes]),
                _int_or_default(row[col_dia])
            )
            id_tiempo = _obtener_o_crear_id_tiempo(fecha_venta)

            registros_a_insertar.append(FactVentas(
                id_tiempo=id_tiempo,
                id_distribuidor=distribuidor.id_distribuidor,
                id_municipio=distribuidor.id_municipio,
                nombre_archivo=nombre_archivo_lote,
                fecha_carga=fecha_carga_lote,
                sorteo=_int_or_default(row[columnas_mapeadas['sorteo']]),
                cantidad_despachada=_int_or_default(row.get(columnas_mapeadas.get('despachada'))),
                cantidad_devuelta=_int_or_default(row.get(columnas_mapeadas.get('devuelta'))),
                cantidad_vendida=_int_or_default(row.get(columnas_mapeadas.get('vendida'))),
                bruto_despacho=_float_or_default(row.get(columnas_mapeadas.get('bruto_despacho'))),
                bruto_devuelto=_float_or_default(row.get(columnas_mapeadas.get('bruto_devuelto'))),
                bruto_vendido=_float_or_default(row.get(columnas_mapeadas.get('bruto_vendido'))),
                neto_vendido=_float_or_default(row.get(columnas_mapeadas.get('neto_vendido'))),
                porcentaje_comision=_float_or_default(row.get(columnas_mapeadas.get('porcentaje')), 25.0)
            ))

        if not registros_a_insertar:
            return jsonify({
                'ok': False,
                'error': 'No se generaron registros válidos para guardar. Verifique distribuidores y municipios asociados.'
            }), 400

        db.session.add_all(registros_a_insertar)

        # Registro inmutable de auditoria: evento de CARGA por lote.
        db.session.add(ETLProjectLog(
            action='CARGA',
            nombre_archivo=nombre_archivo_lote,
            fecha_carga_archivo=fecha_carga_lote,
            registros_afectados=len(registros_a_insertar),
            user_id=current_user.id
        ))

        db.session.commit()

        temp_path = upload_data.get('data_path')
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        nombre_archivo = upload_data.get('filename', '')
        session.pop('upload_data', None)

        return jsonify({
            'ok': True,
            'mensaje': f'¡Archivo "{nombre_archivo}" cargado exitosamente! Registros insertados: {len(registros_a_insertar)}',
            'registros': len(registros_a_insertar)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': f'Error al confirmar la carga: {str(e)}'}), 500


@etl_bp.route('/historial')
@login_required
def historial():
    """Historial consolidado por lote de carga ETL."""
    # Filtra solo filas de CARGA para el nuevo modelo de historial por lote.
    # Los registros de ELIMINACION (modelo anterior) quedan ocultos en la UI.
    logs = ETLProjectLog.query.filter_by(action='CARGA').join(
        Users, ETLProjectLog.user_id == Users.id
    ).order_by(ETLProjectLog.upload_date.desc()).all()

    return render_template(
        'etl/historial.html',
        logs=logs,
        es_admin_auditoria=_es_admin_auditoria(current_user)
    )


@etl_bp.route('/eliminar_carga', methods=['POST'])
@login_required
def eliminar_carga():
    """
    Reversion administrativa de un lote de carga.

    AUDITORÍA: En lugar de insertar una fila nueva de ELIMINACION, se actualiza
    la fila original del lote (esta_activo=False, eliminado_en, eliminado_por_id),
    mejorando la integridad referencial al mantener el ciclo de vida completo
    del lote en una sola linea de la tabla de auditoria.
    """
    if not _es_admin_auditoria(current_user):
        flash('No tiene permisos para eliminar cargas.', 'danger')
        return redirect(url_for('etl.historial'))

    log_id = request.form.get('log_id', '').strip()
    if not log_id:
        flash('Solicitud incompleta: falta el identificador del lote.', 'danger')
        return redirect(url_for('etl.historial'))

    log = db.session.get(ETLProjectLog, int(log_id))
    if not log or log.action != 'CARGA' or not log.esta_activo:
        flash('El lote no existe o ya fue eliminado.', 'danger')
        return redirect(url_for('etl.historial'))

    try:
        from app.models import FactVentas

        registros_eliminados = FactVentas.query.filter_by(
            nombre_archivo=log.nombre_archivo,
            fecha_carga=log.fecha_carga_archivo
        ).delete(synchronize_session=False)

        # Actualiza la fila original del lote en lugar de crear una fila nueva.
        log.esta_activo = False
        log.eliminado_en = _ahora_bogota()
        log.eliminado_por_id = current_user.id

        db.session.commit()
        flash(f'Eliminacion ejecutada. Registros afectados: {registros_eliminados}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la carga: {str(e)}', 'danger')

    return redirect(url_for('etl.historial'))


