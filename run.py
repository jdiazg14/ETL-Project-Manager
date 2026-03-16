"""
Punto de entrada de la aplicación.
Ejecutar con: python run.py
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from app import create_app
from app.models import db, Users, Role

# Crear aplicación

app = create_app()


# Crear usuario admin automáticamente si la tabla Users está vacía (ejecutar al iniciar la app)
def create_initial_admin():
    if Users.query.count() == 0:
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print('No existe el rol "admin" en la tabla role. Inserte el rol primero.')
            return
        admin_password = os.environ.get('INITIAL_ADMIN_PASSWORD')
        if not admin_password:
            print('No se creó el usuario admin inicial: defina INITIAL_ADMIN_PASSWORD en el archivo .env.')
            return
        admin = Users(
            username='admin',
            email='admin@empresa.com',
            role_id=admin_role.id,
            is_active=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print('Usuario administrador inicial creado: admin / contraseña definida por la variable de entorno INITIAL_ADMIN_PASSWORD')

# Ejecutar la función justo después de crear la app
with app.app_context():
    create_initial_admin()


@app.shell_context_processor
def make_shell_context():
    """Crear contexto para Flask shell."""
    return {
        'db': db,
        'Users': Users,
    }


if __name__ == '__main__':
    # Crear directorio de uploads si no existe
    with app.app_context():
        os.makedirs('uploads', exist_ok=True)
    # Ejecutar servidor Flask
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
