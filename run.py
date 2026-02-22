"""
Punto de entrada de la aplicación.
Ejecutar con: python run.py
"""
import os
from dotenv import load_dotenv
from flask import redirect, url_for, render_template

# Cargar variables de entorno
load_dotenv()

from app import create_app
from app.models import db, Users, Role

# Crear aplicación
app = create_app()


@app.route('/')
def main_index():
    """Redirigir a la página principal."""
    from flask_login import current_user
    if current_user.is_authenticated:
        return redirect(url_for('etl.upload'))
    return redirect(url_for('auth.login'))


@app.shell_context_processor
def make_shell_context():
    """Crear contexto para Flask shell."""
    return {
        'db': db,
        'Users': Users,
    }



@app.cli.command()
def create_admin():
    """Crear un usuario administrador según el esquema."""
    username = input('Ingrese nombre de usuario admin: ')
    email = input('Ingrese correo electrónico: ')
    password = input('Ingrese contraseña: ')

    if Users.query.filter_by(username=username).first():
        print(f'El usuario "{username}" ya existe.')
        return

    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print('No existe el rol "admin" en la tabla role. Inserte el rol primero.')
        return

    admin = Users(
        username=username,
        email=email,
        role_id=admin_role.id,
        is_active=True
    )
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    print(f'¡Usuario administrador "{username}" creado exitosamente!')


if __name__ == '__main__':
    # Crear directorio de uploads si no existe
    with app.app_context():
        os.makedirs('uploads', exist_ok=True)
    # Ejecutar servidor Flask
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
