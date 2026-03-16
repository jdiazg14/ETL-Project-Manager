"""Rutas del blueprint de autenticación"""
from urllib.parse import urlparse, urljoin
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth.forms import RegistroForm, LoginForm
from app.models import db, Users
from . import auth_bp


def _is_safe_redirect_target(target):
    """Permite redirigir solo a rutas locales del mismo host."""
    if not target:
        return False

    host_url = request.host_url
    test_url = urlparse(urljoin(host_url, target))
    ref_url = urlparse(host_url)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Página de registro de usuario."""
    if current_user.is_authenticated:
        return redirect(url_for('etl.upload'))
    
    form = RegistroForm()
    
    if form.validate_on_submit():
        # Crear nuevo usuario
        from app.models import Role
        operador_role = Role.query.filter_by(name='operador').first()
        user = Users(
            username=form.username.data,
            email=form.email.data,
            role_id=operador_role.id if operador_role else None
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('¡Registro exitoso! Ahora puede iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('registro.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    if current_user.is_authenticated:
        return redirect(url_for('etl.upload'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Esta cuenta está desactivada.', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Redirigir a la siguiente página o a la página principal
        next_page = request.args.get('next')
        if next_page and _is_safe_redirect_target(next_page):
            return redirect(next_page)
        
        return redirect(url_for('etl.upload'))
    
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión."""
    logout_user()
    flash('Ha cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))
