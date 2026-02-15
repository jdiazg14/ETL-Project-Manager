"""Rutas del blueprint de configuración y dashboard"""
from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app.models import db, User, Role, ETLProjectLog
from . import config_bp


@config_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard de administración.
    Solo accesible para administradores.
    """
    if not current_user.is_admin():
        flash('No tiene permisos para acceder a esta página.', 'danger')
        return redirect(url_for('etl.upload'))
    
    # Estadísticas generales
    total_usuarios = User.query.count()
    admin_role = Role.query.filter_by(name='admin').first()
    analista_role = Role.query.filter_by(name='analista').first()
    total_admins = User.query.filter_by(role_id=admin_role.id if admin_role else None).count()
    total_analistas = User.query.filter_by(role_id=analista_role.id if analista_role else None).count()

    # Estadísticas de logs de carga
    total_logs = ETLProjectLog.query.count()
    logs_procesados = ETLProjectLog.query.filter_by(status='processed').count()
    logs_error = ETLProjectLog.query.filter_by(status='error').count()
    latest_logs = ETLProjectLog.query.order_by(desc(ETLProjectLog.upload_date)).limit(10).all()

    # Estado actual de conexión a DB
    try:
        db.session.execute('SELECT 1')
        db_connected = True
        db_status = 'Conectado'
    except Exception as e:
        db_connected = False
        db_status = f'Error: {str(e)}'

    contexto = {
        'total_usuarios': total_usuarios,
        'total_admins': total_admins,
        'total_analistas': total_analistas,
        'total_logs': total_logs,
        'logs_procesados': logs_procesados,
        'logs_error': logs_error,
        'latest_logs': latest_logs,
        'db_connected': db_connected,
        'db_status': db_status,
    }
    return render_template('dashboard.html', **contexto)


@config_bp.route('/usuarios')
@login_required
def lista_usuarios():
    """
    Lista de usuarios del sistema.
    Solo accesible para administradores.
    """
    if not current_user.is_admin():
        flash('No tiene permisos para acceder a esta página.', 'danger')
        return redirect(url_for('etl.upload'))
    
    usuarios = User.query.all()
    return render_template('usuarios.html', usuarios=usuarios)


@config_bp.route('/db-status')
@login_required
def db_status():
    """
    Página de estado de la conexión a la base de datos.
    """
    if not current_user.is_admin():
        flash('No tiene permisos para acceder a esta página.', 'danger')
        return redirect(url_for('etl.upload'))
    
    db_config = {
        'host': current_app.config['DB_HOST'],
        'port': current_app.config['DB_PORT'],
        'database': current_app.config['DB_NAME'],
        'user': current_app.config['DB_USER'],
    }
    
    try:
        result = db.session.execute('SELECT version()')
        db_version = result.scalar()
        db_connected = True
        db_error = None
    except Exception as e:
        db_connected = False
        db_version = None
        db_error = str(e)
    
    contexto = {
        'db_config': db_config,
        'db_connected': db_connected,
        'db_version': db_version,
        'db_error': db_error,
    }
    
    return render_template('db_status.html', **contexto)
