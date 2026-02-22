from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.config.decorators import admin_required
from sqlalchemy import func, desc, text
from app.models import db, Users, Role, ETLProjectLog
from app.models import DimDepartamento, DimMunicipio, DimDistribuidor
from app.config.forms import UsuarioForm
from app.config.forms import DepartamentoForm, MunicipioForm, DistribuidorForm
from app.config.role_forms import RoleForm

# DEFINICIÓN DEL BLUEPRINT
config_bp = Blueprint('config', __name__, url_prefix='/config', template_folder='../templates/config')

# --- DASHBOARD ADMINISTRATIVO ---
@config_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_usuarios = Users.query.count()
    admin_role = Role.query.filter_by(name='admin').first()
    analista_role = Role.query.filter_by(name='analista').first()
    total_admins = Users.query.filter_by(role_id=admin_role.id if admin_role else None).count()
    total_analistas = Users.query.filter_by(role_id=analista_role.id if analista_role else None).count()
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
    usuarios = Users.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@config_bp.route('/usuarios/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_usuario(user_id):
    user = Users.query.get_or_404(user_id)
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
        existing_user = Users.query.filter((Users.username == form.username.data) | (Users.email == form.email.data)).first()
        if existing_user:
            flash('El usuario o correo electrónico ya existe.', 'danger')
            return render_template('usuario_form.html', form=form, crear=True)
        user = Users(
            username=form.username.data,
            email=form.email.data,
            role_id=form.role_id.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
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
    user = Users.query.get_or_404(user_id)
    form = UsuarioForm(obj=user)
    if form.validate_on_submit():
        # Pre-commit validation: check for duplicate username/email (excluding current user)
        existing_user = Users.query.filter(
            ((Users.username == form.username.data) | (Users.email == form.email.data)) & (Users.id != user.id)
        ).first()
        if existing_user:
            flash('El usuario o correo electrónico ya existe.', 'danger')
            return render_template('usuario_form.html', form=form, crear=False)
        user.username = form.username.data
        user.email = form.email.data
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        # Solo actualizar contraseña si se ingresa una nueva
        if form.password.data:
            user.set_password(form.password.data)
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
    user = Users.query.get_or_404(user_id)
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

# --- DEPARTAMENTOS ---
@config_bp.route('/departamentos')
@login_required
@admin_required
def lista_departamentos():
    departamentos = DimDepartamento.query.all()
    return render_template('departamentos.html', departamentos=departamentos)

@config_bp.route('/departamentos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_departamento():
    form = DepartamentoForm()
    if form.validate_on_submit():
        existing = DimDepartamento.query.filter_by(id_departamento=form.id_departamento.data).first()
        if existing:
            flash('El código de departamento ya existe.', 'danger')
            return render_template('departamento_form.html', form=form, crear=True)
        departamento = DimDepartamento(
            id_departamento=form.id_departamento.data,
            nombre_depto=form.nombre_depto.data
        )
        db.session.add(departamento)
        try:
            db.session.commit()
            flash('Departamento creado correctamente.', 'success')
            return redirect(url_for('config.lista_departamentos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear departamento: {str(e)}', 'danger')
    return render_template('departamento_form.html', form=form, crear=True)

@config_bp.route('/departamentos/<id_departamento>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_departamento(id_departamento):
    departamento = DimDepartamento.query.get_or_404(id_departamento)
    form = DepartamentoForm(obj=departamento)
    if form.validate_on_submit():
        departamento.nombre_depto = form.nombre_depto.data
        try:
            db.session.commit()
            flash('Departamento actualizado correctamente.', 'success')
            return redirect(url_for('config.lista_departamentos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar departamento: {str(e)}', 'danger')
    return render_template('departamento_form.html', form=form, crear=False)

@config_bp.route('/departamentos/<id_departamento>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_departamento(id_departamento):
    departamento = DimDepartamento.query.get_or_404(id_departamento)
    db.session.delete(departamento)
    db.session.commit()
    flash('Departamento eliminado correctamente.', 'success')
    return redirect(url_for('config.lista_departamentos'))

# --- MUNICIPIOS ---
@config_bp.route('/municipios')
@login_required
@admin_required
def lista_municipios():
    municipios = DimMunicipio.query.all()
    return render_template('municipios.html', municipios=municipios)

@config_bp.route('/municipios/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_municipio():
    form = MunicipioForm()
    form.id_departamento.choices = [(d.id_departamento, d.nombre_depto) for d in DimDepartamento.query.all()]
    if form.validate_on_submit():
        existing = DimMunicipio.query.filter_by(id_municipio=form.id_municipio.data).first()
        if existing:
            flash('El código de municipio ya existe.', 'danger')
            return render_template('municipio_form.html', form=form, crear=True)
        municipio = DimMunicipio(
            id_municipio=form.id_municipio.data,
            id_departamento=form.id_departamento.data,
            nombre_municipio=form.nombre_municipio.data
        )
        db.session.add(municipio)
        try:
            db.session.commit()
            flash('Municipio creado correctamente.', 'success')
            return redirect(url_for('config.lista_municipios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear municipio: {str(e)}', 'danger')
    return render_template('municipio_form.html', form=form, crear=True)

@config_bp.route('/municipios/<id_municipio>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_municipio(id_municipio):
    municipio = DimMunicipio.query.get_or_404(id_municipio)
    form = MunicipioForm(obj=municipio)
    form.id_departamento.choices = [(d.id_departamento, d.nombre_depto) for d in DimDepartamento.query.all()]
    if form.validate_on_submit():
        municipio.id_departamento = form.id_departamento.data
        municipio.nombre_municipio = form.nombre_municipio.data
        try:
            db.session.commit()
            flash('Municipio actualizado correctamente.', 'success')
            return redirect(url_for('config.lista_municipios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar municipio: {str(e)}', 'danger')
    return render_template('municipio_form.html', form=form, crear=False)

@config_bp.route('/municipios/<id_municipio>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_municipio(id_municipio):
    municipio = DimMunicipio.query.get_or_404(id_municipio)
    db.session.delete(municipio)
    db.session.commit()
    flash('Municipio eliminado correctamente.', 'success')
    return redirect(url_for('config.lista_municipios'))

# --- DISTRIBUIDORES ---
@config_bp.route('/distribuidores')
@login_required
@admin_required
def lista_distribuidores():
    distribuidores = DimDistribuidor.query.all()
    return render_template('distribuidores.html', distribuidores=distribuidores)

@config_bp.route('/distribuidores/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_distribuidor():
    form = DistribuidorForm()
    form.id_municipio.choices = [(m.id_municipio, m.nombre_municipio) for m in DimMunicipio.query.all()]
    if form.validate_on_submit():
        existing = DimDistribuidor.query.filter_by(codigo_sucursal=form.codigo_sucursal.data).first()
        if existing:
            flash('El código de sucursal ya existe.', 'danger')
            return render_template('distribuidor_form.html', form=form, crear=True)
        distribuidor = DimDistribuidor(
            codigo_sucursal=form.codigo_sucursal.data,
            nombre_sucursal=form.nombre_sucursal.data,
            nit=form.nit.data,
            razon_social=form.razon_social.data,
            cupo_asignado=form.cupo_asignado.data,
            grupo=form.grupo.data,
            id_municipio=form.id_municipio.data,
            activo=form.activo.data
        )
        db.session.add(distribuidor)
        try:
            db.session.commit()
            flash('Distribuidor creado correctamente.', 'success')
            return redirect(url_for('config.lista_distribuidores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear distribuidor: {str(e)}', 'danger')
    return render_template('distribuidor_form.html', form=form, crear=True)

@config_bp.route('/distribuidores/<int:id_distribuidor>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_distribuidor(id_distribuidor):
    distribuidor = DimDistribuidor.query.get_or_404(id_distribuidor)
    form = DistribuidorForm(obj=distribuidor)
    form.id_municipio.choices = [(m.id_municipio, m.nombre_municipio) for m in DimMunicipio.query.all()]
    if form.validate_on_submit():
        distribuidor.codigo_sucursal = form.codigo_sucursal.data
        distribuidor.nombre_sucursal = form.nombre_sucursal.data
        distribuidor.nit = form.nit.data
        distribuidor.razon_social = form.razon_social.data
        distribuidor.cupo_asignado = form.cupo_asignado.data
        distribuidor.grupo = form.grupo.data
        distribuidor.id_municipio = form.id_municipio.data
        distribuidor.activo = form.activo.data
        try:
            db.session.commit()
            flash('Distribuidor actualizado correctamente.', 'success')
            return redirect(url_for('config.lista_distribuidores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar distribuidor: {str(e)}', 'danger')
    return render_template('distribuidor_form.html', form=form, crear=False)

@config_bp.route('/distribuidores/<int:id_distribuidor>/eliminar', methods=['POST'])
@login_required
@admin_required
def eliminar_distribuidor(id_distribuidor):
    distribuidor = DimDistribuidor.query.get_or_404(id_distribuidor)
    db.session.delete(distribuidor)
    db.session.commit()
    flash('Distribuidor eliminado correctamente.', 'success')
    return redirect(url_for('config.lista_distribuidores') )
