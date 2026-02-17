from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.config.decorators import admin_required
from sqlalchemy import func, desc, text
from app.models import db, User, Role, ETLProjectLog
from app.config.forms import UsuarioForm
from app.config.role_forms import RoleForm

# DEFINICIÓN DEL BLUEPRINT
config_bp = Blueprint('config', __name__, url_prefix='/config', template_folder='../templates/config')

# --- DASHBOARD ADMINISTRATIVO ---
@config_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_usuarios = User.query.count()
    admin_role = Role.query.filter_by(name='admin').first()
    analista_role = Role.query.filter_by(name='analista').first()
    total_admins = User.query.filter_by(role_id=admin_role.id if admin_role else None).count()
    total_analistas = User.query.filter_by(role_id=analista_role.id if analista_role else None).count()
    total_logs = ETLProjectLog.query.count()
    logs_procesados = ETLProjectLog.query.filter_by(status='processed').count()
    logs_error = ETLProjectLog.query.filter_by(status='error').count()
    latest_logs = ETLProjectLog.query.order_by(ETLProjectLog.upload_date.desc()).limit(10).all()
    try:
        db.session.execute(text('SELECT 1'))
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
        'uploads_error': logs_error,
        'latest_logs': latest_logs,
        'db_connected': db_connected,
        'db_status': db_status,
    }
    return render_template('dashboard.html', **contexto)

# --- USUARIOS ---
@config_bp.route('/usuarios')
@login_required
@admin_required
def lista_usuarios():
    usuarios = User.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@config_bp.route('/usuarios/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_usuario(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"Usuario {'activado' if user.is_active else 'desactivado'} correctamente.", 'success')
    return redirect(url_for('config.lista_usuarios'))

@config_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    form = UsuarioForm()
    if form.validate_on_submit():
        # Pre-commit validation: check for duplicate username/email
        existing_user = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
        if existing_user:
            flash('El usuario o correo electrónico ya existe.', 'danger')
            return render_template('usuario_form.html', form=form, crear=True)
        user = User(
            username=form.username.data,
            email=form.email.data,
            role_id=form.role_id.data,
            is_active=form.is_active.data
        )
        user.set_password('temporal123')
        db.session.add(user)
        try:
            db.session.commit()
            flash('Usuario creado correctamente.', 'success')
            return redirect(url_for('config.lista_usuarios'))
        except Exception as e:
            db.session.rollback()
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError):
                flash('Error de integridad: el usuario o correo ya existe.', 'danger')
            else:
                flash(f'Error al crear usuario: {str(e)}', 'danger')
    return render_template('usuario_form.html', form=form, crear=True)

@config_bp.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    form = UsuarioForm(obj=user)
    if form.validate_on_submit():
        # Pre-commit validation: check for duplicate username/email (excluding current user)
        existing_user = User.query.filter(
            ((User.username == form.username.data) | (User.email == form.email.data)) & (User.id != user.id)
        ).first()
        if existing_user:
            flash('El usuario o correo electrónico ya existe.', 'danger')
            return render_template('usuario_form.html', form=form, crear=False)
        user.username = form.username.data
        user.email = form.email.data
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        try:
            db.session.commit()
            flash('Usuario actualizado correctamente.', 'success')
            return redirect(url_for('config.lista_usuarios'))
        except Exception as e:
            db.session.rollback()
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError):
                flash('Error de integridad: el usuario o correo ya existe.', 'danger')
            else:
                flash(f'Error al actualizar usuario: {str(e)}', 'danger')
    return render_template('usuario_form.html', form=form, crear=False)

@config_bp.route('/usuarios/<int:user_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado correctamente.', 'success')
    return redirect(url_for('config.lista_usuarios'))

# --- ROLES ---
@config_bp.route('/roles')
@login_required
@admin_required
def lista_roles():
    roles = Role.query.all()
    return render_template('roles.html', roles=roles)

@config_bp.route('/roles/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_role():
    form = RoleForm()
    if form.validate_on_submit():
        # Pre-commit validation: check for duplicate role name
        existing_role = Role.query.filter_by(name=form.name.data).first()
        if existing_role:
            flash('El nombre del rol ya existe.', 'danger')
            return render_template('role_form.html', form=form, crear=True)
        role = Role(name=form.name.data, description=form.description.data)
        db.session.add(role)
        try:
            db.session.commit()
            flash('Rol creado correctamente.', 'success')
            return redirect(url_for('config.lista_roles'))
        except Exception as e:
            db.session.rollback()
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError):
                flash('Error de integridad: el nombre del rol ya existe.', 'danger')
            else:
                flash(f'Error al crear rol: {str(e)}', 'danger')
    return render_template('role_form.html', form=form, crear=True)

@config_bp.route('/roles/<int:role_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        # Pre-commit validation: check for duplicate role name (excluding current role)
        existing_role = Role.query.filter(Role.name == form.name.data, Role.id != role.id).first()
        if existing_role:
            flash('El nombre del rol ya existe.', 'danger')
            return render_template('role_form.html', form=form, crear=False)
        role.name = form.name.data
        role.description = form.description.data
        try:
            db.session.commit()
            flash('Rol actualizado correctamente.', 'success')
            return redirect(url_for('config.lista_roles'))
        except Exception as e:
            db.session.rollback()
            from sqlalchemy.exc import IntegrityError
            if isinstance(e, IntegrityError):
                flash('Error de integridad: el nombre del rol ya existe.', 'danger')
            else:
                flash(f'Error al actualizar rol: {str(e)}', 'danger')
    return render_template('role_form.html', form=form, crear=False)

@config_bp.route('/roles/<int:role_id>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_role(role_id):
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash('Rol eliminado correctamente.', 'success')
    return redirect(url_for('config.lista_roles'))