"""
Inicialización de la aplicación Flask.
Configura extensiones, modelos, blueprints y login_manager.
"""
from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager, current_user
from config import config
from app.models import db, Users
import os


def create_app(config_class=None):
    """
    Factory function para crear la aplicación Flask.
    
    Args:
        config_class: Clase de configuración a usar.
                     Si no se especifica, usa la del ambiente.
    
    Returns:
        app: Instancia de Flask configurada
    """
    app = Flask(__name__)
    
    # Cargar configuración
    if config_class is None:
        app.config.from_object(config)
    else:
        app.config.from_object(config_class)

    # Hardening: evita iniciar sin variables críticas en ambientes reales.
    if not app.config.get('TESTING'):
        if not app.config.get('SECRET_KEY'):
            raise RuntimeError('SECRET_KEY no configurada. Defina la variable de entorno SECRET_KEY.')
        if not app.config.get('SQLALCHEMY_DATABASE_URI'):
            raise RuntimeError('DATABASE_URL no configurada. Defina la variable de entorno DATABASE_URL.')
    
    # Crear carpeta de uploads si no existe
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Configurar Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))
    
    # Registrar blueprints
    from app.auth.routes import auth_bp
    from app.config.routes import config_bp
    from app.etl.routes import etl_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(etl_bp)
    
    # Ruta raíz
    @app.route('/')
    def index():
        """Redirigir a la página principal."""
        if current_user.is_authenticated:
            return redirect(url_for('etl.upload'))
        return redirect(url_for('auth.login'))
    
    # Nota: La inicialización/creación de tablas debe manejarse fuera
    # del arranque de la aplicación (migraciones o scripts separados).
    
    # Manejadores de errores
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403
    
    @app.errorhandler(500)
    def server_error(error):
        return render_template('500.html'), 500
    
    return app
