"""Rutas del blueprint ETL"""
import os
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import json
from app.models import db, ETLProjectLog
from app.etl.processors import DataProcessor
from . import etl_bp


@etl_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """
    Página principal de carga de archivos.
    GET: Mostrar formulario
    POST: Procesar archivo cargado
    """
    if request.method == 'GET':
        return render_template('upload.html')
    
    # Procesamiento POST
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('etl.upload'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('etl.upload'))
    
    if not DataProcessor.allowed_file(file.filename):
        flash('Formato de archivo no permitido. Use CSV o Excel.', 'danger')
        return redirect(url_for('etl.upload'))
    
    try:
        from io import BytesIO
        file_bytes = file.read()
        file_stream = BytesIO(file_bytes)
        df, error = DataProcessor.read_file(file_stream, filename=file.filename)
        if error:
            flash(f'Error al leer el archivo: {error}', 'danger')
            return redirect(url_for('etl.upload'))
        tabla = df.head(10).to_html(classes='table table-striped', index=False)
        return render_template('preview.html', filename=file.filename, tabla=tabla)
    except Exception as e:
        flash(f'Error al procesar el archivo: {str(e)}', 'danger')
        return redirect(url_for('etl.upload'))


@etl_bp.route('/confirm-upload', methods=['POST'])
@login_required
def confirm_upload():
    """
    Confirmar la carga de datos (guardar en DB).
    """
    if 'upload_data' not in session:
        flash('Sesión expirada. Intente nuevamente.', 'danger')
        return redirect(url_for('etl.upload'))
    
    try:
        upload_data = session['upload_data']
        file_path = upload_data['file_path']
        
        # Registrar la carga en la base de datos
        data_upload = DataUpload(
            user_id=current_user.id,
            filename=os.path.basename(file_path),
            original_filename=upload_data['filename'],
            file_path=file_path,
            file_size=upload_data['file_size'],
            file_type=upload_data['file_type'],
            total_rows=upload_data['total_rows'],
            total_columns=upload_data['total_columns'],
            status='processed'
        )
        
        db.session.add(data_upload)
        db.session.commit()
        
        # Limpiar sesión
        session.pop('upload_data', None)
        
        flash(f'¡Archivo "{upload_data["filename"]}" cargado exitosamente!', 'success')
        return redirect(url_for('etl.historial'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al confirmadas la carga: {str(e)}', 'danger')
        return redirect(url_for('etl.upload'))


@etl_bp.route('/historial')
@login_required
def historial():
    from flask import flash, redirect, url_for
    flash('Función en desarrollo', 'warning')
    return redirect(url_for('config.dashboard'))


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
