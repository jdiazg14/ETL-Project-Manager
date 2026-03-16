"""Configuration module for catalogs, users, and dashboard routes."""
from flask import Blueprint

config_bp = Blueprint('config', __name__, url_prefix='/config', template_folder='../templates/config')

