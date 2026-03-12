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
from app.models import db, ETLProjectLog, Users
from app.etl.processors import DataProcessor
from . import etl_bp


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
    'normalizaciones' es una lista de mensajes informativos sobre
    columnas reconocidas por nombres alternativos (sinónimos históricos).
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
                # registrar la normalización para feedback al usuario.
                if variante != col_estandar:
                    normalizaciones.append(
                        f"Columna '{variante}' reconocida y normalizada como '{col_estandar}'"
                    )
                break
    return columnas_mapeadas, normalizaciones


def _validar_integridad_entrada(df, columnas_mapeadas):
    """
    ETAPA 1: INTEGRIDAD DE ENTRADA.

    Controles aplicados:
    - Control de duplicidad de sorteos.
    - Verificación contra maestro de distribuidores.
    - Validación de fechas Año/Mes/Día parseables.
    """
    reporte_errores = {}

    # Control de duplicidad de sorteos (integridad por lote).
    col_sorteo = columnas_mapeadas['sorteo']
    sorteos_archivo = [int(v) for v in df[col_sorteo].dropna().unique().tolist()]
    if sorteos_archivo:
        from app.models import FactVentas
        sorteo_existente = FactVentas.query.filter(FactVentas.sorteo.in_(sorteos_archivo)).first()
        if sorteo_existente:
            reporte_errores['sorteo'] = f'El sorteo {sorteo_existente.sorteo} ya ha sido cargado'

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
        reporte_errores['distribuidores_faltantes'] = codigos_faltantes

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
        reporte_errores['tiempo'] = (
            'Hay fechas inválidas en columnas Año/Mes/Día. '
            f'Filas: {", ".join(str(f) for f in errores_tiempo[:20])}'
        )

    return reporte_errores


def _auditar_integridad_aritmetica(df, columnas_mapeadas):
    """
    ETAPA 2: REGLAS DE NEGOCIO (auditoría de integridad aritmética).

    Fórmulas auditadas por fila:
    1) Despachada - Devuelta == Vendida
    2) Bruto despacho - Bruto devuelto == Bruto vendido
    3) Neto vendido == (Bruto vendido * (100 - Porcentaje) / 100)
    """
    errores = []
    tolerancia = 0.01

    for idx, row in df.iterrows():
        fila_excel = idx + 2

        despachada = float(row[columnas_mapeadas['despachada']])
        devuelta = float(row[columnas_mapeadas['devuelta']])
        vendida = float(row[columnas_mapeadas['vendida']])
        bruto_despacho = float(row[columnas_mapeadas['bruto_despacho']])
        bruto_devuelto = float(row[columnas_mapeadas['bruto_devuelto']])
        bruto_vendido = float(row[columnas_mapeadas['bruto_vendido']])
        neto_vendido = float(row[columnas_mapeadas['neto_vendido']])
        porcentaje = float(row[columnas_mapeadas['porcentaje']])

        if abs((despachada - devuelta) - vendida) > tolerancia:
            errores.append(
                f'Fila {fila_excel}: Inconsistencia en Cantidades (Despachada - Devuelta != Vendida)'
            )

        if abs((bruto_despacho - bruto_devuelto) - bruto_vendido) > tolerancia:
            errores.append(
                f'Fila {fila_excel}: Inconsistencia en Brutos (Bruto despacho - Bruto devuelto != Bruto vendido)'
            )

        neto_calculado = bruto_vendido * (100 - porcentaje) / 100
        if abs(neto_vendido - neto_calculado) > tolerancia:
            errores.append(
                f'Fila {fila_excel}: Inconsistencia en Neto Vendido (Neto vendido != Bruto vendido * (100 - Porcentaje) / 100)'
            )

    return errores


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
    
    # ========================================================================
    # PROCESAMIENTO POST: VALIDACIÓN POR CAPAS
    # ========================================================================
    
    # --- Validación Inicial: Archivo recibido ---
    if 'file' not in request.files:
        return jsonify({'error': 'No se seleccionó ningún archivo.'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo.'}), 400
    
    if not DataProcessor.allowed_file(file.filename):
        return jsonify({'error': 'Formato de archivo no permitido. Use CSV o Excel.'}), 400
    
    try:
        # --- Lectura del archivo ---
        from io import BytesIO
        file_bytes = file.read()
        file_stream = BytesIO(file_bytes)
        df, error = DataProcessor.read_file(file_stream, filename=file.filename)
        
        if error:
            return jsonify({'error': f'Error al leer el archivo: {error}'}), 400

        # ====================================================================
        # CAPA 1: VALIDACIONES PREVIAS (PANDAS)
        # Objetivo: Verificar integridad estructural antes de consultar BD
        # ====================================================================
        
        reporte_errores = {}
        reporte_avisos = []
        
        # --- 1.1. Normalizar nombres de columnas ---
        # Eliminar espacios y convertir a minúsculas para comparación robusta
        df.columns = df.columns.str.strip().str.lower()
        
        # --- 1.2. Mapeo de columnas esperadas ---
        # _mapear_columnas retorna (mapa, normalizaciones) donde 'normalizaciones'
        # lista los sinónimos históricos que fueron detectados y normalizados.
        columnas_mapeadas, normalizaciones_alias = _mapear_columnas(df)
        if normalizaciones_alias:
            reporte_avisos.extend(normalizaciones_alias)

        # --- 1.2.1. Porcentaje ausente: auto-creación con valor por defecto ---
        # Si el archivo no contiene la columna Porcentaje (ni ningún sinónimo),
        # se crea con el valor operativo 25.0 para que la fórmula del Neto
        # Vendido tenga un operando válido en la ETAPA 2 (Reglas de Negocio).
        if 'porcentaje' not in columnas_mapeadas:
            df['porcentaje'] = 25.0
            columnas_mapeadas['porcentaje'] = 'porcentaje'
            reporte_avisos.append(
                'Columna "Porcentaje" no encontrada en el archivo; '
                'se asignó automáticamente el valor 25.0 para todos los registros.'
            )

        # Verificar que existan al menos las columnas críticas.
        # 'porcentaje' se excluye de esta lista porque se auto-completa arriba.
        columnas_criticas = [
            'anio', 'mes', 'dia', 'sorteo', 'distribuidor',
            'despachada', 'devuelta', 'vendida',
            'bruto_despacho', 'bruto_devuelto', 'bruto_vendido',
            'neto_vendido',
        ]
        columnas_faltantes = [col for col in columnas_criticas if col not in columnas_mapeadas]

        if columnas_faltantes:
            reporte_errores['formato'] = f'Faltan columnas críticas en el archivo: {", ".join(columnas_faltantes)}'
            return jsonify(reporte_errores), 400
        
        # --- 1.3. Validación de valores nulos en columnas críticas ---
        # METODOLOGÍA: Esta validación previene inconsistencias antes de la persistencia
        errores_nulos = []
        for col_estandar in columnas_criticas:
            col_real = columnas_mapeadas[col_estandar]
            nulos_count = df[col_real].isna().sum()
            if nulos_count > 0:
                errores_nulos.append(f'{col_estandar.capitalize()}: {nulos_count} valores nulos')
        
        if errores_nulos:
            reporte_errores['valores_nulos'] = errores_nulos
        
        # --- 1.4. Validación estricta y transformación numérica ---
        # METODOLOGÍA: Endurece la fase de Transformación para bloquear datos corruptos.
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
            reporte_errores['formato'] = (
                'Error de Formato: Se encontraron valores no numéricos en las '
                'columnas de montos. Por favor revisa el archivo.'
            )
            reporte_errores['formato_detalle'] = errores_formato_numerico

        # --- 1.5. Control de nulos en porcentaje (default operativo) ---
        # Si porcentaje viene nulo, se rellena con 25.0 y se reporta aviso.
        if 'porcentaje' in columnas_mapeadas:
            col_porcentaje = columnas_mapeadas['porcentaje']
            filas_porcentaje_nulo = (df.index[df[col_porcentaje].isna()] + 2).tolist()
            if filas_porcentaje_nulo:
                df[col_porcentaje] = df[col_porcentaje].fillna(25.0)
                reporte_avisos.append(
                    'Se asigno Porcentaje = 25.0 en filas con nulo: '
                    f'{", ".join(str(f) for f in filas_porcentaje_nulo[:20])}'
                )

        # --- 1.6. Control de duplicidad y maestro de distribuidores ---
        errores_integridad_entrada = _validar_integridad_entrada(df, columnas_mapeadas)
        if errores_integridad_entrada:
            reporte_errores.update(errores_integridad_entrada)
        
        # ====================================================================
        # DECISIÓN CAPA 1: RETORNAR ERRORES O MOSTRAR PREVIEW
        # ====================================================================
        
        if reporte_errores:
            # Hay errores de formato: bloquear flujo antes de negocio.
            reporte_errores['bloquear_guardado'] = True
            if reporte_avisos:
                reporte_errores['avisos'] = reporte_avisos
            return jsonify(reporte_errores), 400
        
        # CAPA 1 aprobada: guardar dataset para fase 2 (negocio).
        temp_data_path = _guardar_df_temporal(df)
        session['upload_data'] = {
            'filename': file.filename,
            'data_path': temp_data_path,
            'columnas_mapeadas': columnas_mapeadas,
            'avisos': reporte_avisos,
            'formato_validado': True,
            'negocio_validado': False
        }
        
        # Generar tabla HTML para vista previa
        tabla = df.to_html(classes='table table-striped', index=False)
        return render_template(
            'etl/preview.html',
            filename=file.filename,
            tabla=tabla,
            avisos_integridad=reporte_avisos
        )
        
    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 400


@etl_bp.route('/validate-business', methods=['POST'])
@login_required
def validate_business():
    """ETAPA 2 del ETL: reglas de negocio (integridad aritmética)."""
    upload_data = session.get('upload_data')
    if not upload_data or not upload_data.get('formato_validado'):
        return jsonify({
            'error': 'No hay datos válidos de formato en sesión. Cargue y valide el archivo nuevamente.',
            'bloquear_guardado': True
        }), 400

    try:
        df = _cargar_df_temporal(upload_data.get('data_path'))
        columnas_mapeadas = upload_data.get('columnas_mapeadas', {})

        # Auditoría de integridad aritmética fila por fila.
        errores_aritmetica = _auditar_integridad_aritmetica(df, columnas_mapeadas)
        if errores_aritmetica:
            errores_negocio = {
                'reglas_negocio': errores_aritmetica,
                'bloquear_guardado': True
            }
            upload_data['negocio_validado'] = False
            session['upload_data'] = upload_data
            return jsonify(errores_negocio), 400

        upload_data['negocio_validado'] = True
        session['upload_data'] = upload_data
        payload_ok = {'message': 'Validación de reglas de negocio aprobada.'}
        if upload_data.get('avisos'):
            payload_ok['avisos'] = upload_data.get('avisos')
        return jsonify(payload_ok), 200
    except Exception as e:
        return jsonify({
            'error': f'Error al validar reglas de negocio: {str(e)}',
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
        flash('Sesión expirada. Intente nuevamente.', 'danger')
        return redirect(url_for('etl.upload'))

    if not session['upload_data'].get('negocio_validado'):
        flash('Debe ejecutar la validación de reglas de negocio antes de guardar.', 'danger')
        return redirect(url_for('etl.upload'))
    
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
        fecha_carga_lote = datetime.utcnow()
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
            flash('No se generaron registros válidos para guardar. Verifique distribuidores y municipios asociados.', 'danger')
            return redirect(url_for('etl.upload'))

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

        session.pop('upload_data', None)

        flash(f'¡Archivo "{upload_data.get("filename", "")}" cargado exitosamente! Registros insertados: {len(registros_a_insertar)}', 'success')
        return redirect(url_for('etl.upload'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al confirmar la carga: {str(e)}', 'danger')
        return redirect(url_for('etl.upload'))


@etl_bp.route('/historial')
@login_required
def historial():
    """Historial de auditoria ETL con log inmutable por evento."""
    logs = ETLProjectLog.query.join(
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
    Reversion administrativa por lote de archivo.

    Diseno de Log Inmutable:
    - No se actualizan ni eliminan logs historicos.
    - Cada reversion inserta un nuevo evento ELIMINACION para trazabilidad.
    """
    if not _es_admin_auditoria(current_user):
        flash('No tiene permisos para eliminar cargas.', 'danger')
        return redirect(url_for('etl.historial'))

    nombre_archivo = request.form.get('nombre_archivo', '').strip()
    fecha_carga_raw = request.form.get('fecha_carga_archivo', '').strip()

    if not nombre_archivo or not fecha_carga_raw:
        flash('Solicitud incompleta: faltan datos del lote a eliminar.', 'danger')
        return redirect(url_for('etl.historial'))

    try:
        fecha_carga_archivo = datetime.fromisoformat(fecha_carga_raw)
    except ValueError:
        flash('Formato de fecha de carga invalido para eliminacion.', 'danger')
        return redirect(url_for('etl.historial'))

    try:
        from app.models import FactVentas

        registros_eliminados = FactVentas.query.filter_by(
            nombre_archivo=nombre_archivo,
            fecha_carga=fecha_carga_archivo
        ).delete(synchronize_session=False)

        # Registro inmutable del evento de eliminacion (auditoria obligatoria).
        db.session.add(ETLProjectLog(
            action='ELIMINACION',
            nombre_archivo=nombre_archivo,
            fecha_carga_archivo=fecha_carga_archivo,
            registros_afectados=registros_eliminados,
            user_id=current_user.id
        ))

        db.session.commit()
        flash(f'Eliminacion ejecutada. Registros afectados: {registros_eliminados}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la carga: {str(e)}', 'danger')

    return redirect(url_for('etl.historial'))


@etl_bp.route('/ver/<int:upload_id>')
@login_required
def ver_upload(upload_id):
    """
    Ver detalles de una carga específica.
    """
    upload = DataUpload.query.get_or_404(upload_id)
    
    # Verificar permisos
    if upload.user_id != current_user.id and not current_user.is_admin():
        flash('No tiene permisos para ver este archivo.', 'danger')
        return redirect(url_for('etl.historial'))
    
    # Leer archivo nuevamente para mostrar datos
    df, error = DataProcessor.read_file(upload.file_path)
    
    if error:
        flash(f'Error al leer el archivo: {error}', 'danger')
        return redirect(url_for('etl.historial'))
    
    # Generar tabla HTML para las primeras 10 filas
    tabla = df.head(10).to_html(classes='table table-striped', index=False)
    return render_template('ver_upload.html', upload=upload, preview=preview_info, tabla=tabla)
