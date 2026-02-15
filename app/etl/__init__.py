"""Blueprint de ETL - Carga y procesamiento de datos"""
from flask import Blueprint

etl_bp = Blueprint('etl', __name__, url_prefix='/etl', template_folder='../templates/etl')
