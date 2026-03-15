"""
Modelos de base de datos según schema.sql
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

db = SQLAlchemy()


def _ahora_bogota():
    """Retorna la hora actual en la zona horaria de Bogotá, Colombia (America/Bogota)."""
    tz = pytz.timezone('America/Bogota')
    # Se elimina tzinfo para compatibilidad con columnas DATETIME de MySQL,
    # pero el valor ya corresponde a la hora local colombiana.
    return datetime.now(tz).replace(tzinfo=None)

class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship('Users', backref='role', lazy=True)

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # foreign_keys requerido porque ETLProjectLog tiene dos FK apuntando a users.id.
    logs = db.relationship('ETLProjectLog', foreign_keys='[ETLProjectLog.user_id]', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role and self.role.name == 'admin'

    def __repr__(self):
        return f'<Users {self.username}>'

class ETLProjectLog(db.Model):
    """
    Registro del ciclo de vida completo de cada lote de carga ETL.

    AUDITORÍA: Este diseño mejora la integridad referencial del historial al
    representar cada lote de datos en una sola fila. Las eliminaciones no crean
    filas adicionales; en su lugar actualizan la fila original (esta_activo=False,
    eliminado_en, eliminado_por_id), permitiendo auditar el ciclo de vida completo
    de un lote en una única entrada de la tabla.
    """
    __tablename__ = 'etl_project_logs'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False, default='CARGA')
    nombre_archivo = db.Column(db.String(255), nullable=False)
    fecha_carga_archivo = db.Column(db.DateTime, nullable=False)
    registros_afectados = db.Column(db.Integer, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=_ahora_bogota)
    # Ciclo de vida del lote: permite marcar eliminaciones sin duplicar filas.
    esta_activo = db.Column(db.Boolean, nullable=False, default=True)
    eliminado_en = db.Column(db.DateTime, nullable=True)
    eliminado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('Users', foreign_keys=[user_id], back_populates='logs')
    eliminado_por = db.relationship('Users', foreign_keys=[eliminado_por_id])

    def __repr__(self):
        return f'<ETLProjectLog {self.action} {self.nombre_archivo}>'

# --- Modelos de negocio ---
class DimDepartamento(db.Model):
    __tablename__ = 'Dim_Departamento'
    id_departamento = db.Column(db.String(2), primary_key=True)
    nombre_depto = db.Column(db.String(100), nullable=False)
    municipios = db.relationship('DimMunicipio', backref='departamento', cascade='all, delete-orphan', lazy=True)

class DimMunicipio(db.Model):
    __tablename__ = 'Dim_Municipio'
    id_municipio = db.Column(db.String(5), primary_key=True)
    id_departamento = db.Column(db.String(2), db.ForeignKey('Dim_Departamento.id_departamento', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    nombre_municipio = db.Column(db.String(100), nullable=False)
    distribuidores = db.relationship('DimDistribuidor', backref='municipio', lazy=True)


# --- Nueva tabla: Grupo de Distribuidores ---
class DimGrupoDistribuidor(db.Model):
    __tablename__ = 'Dim_GrupoDistribuidor'
    id_grupo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nit = db.Column(db.String(15), unique=True)
    nombre_grupo = db.Column(db.String(100), nullable=False)
    plan = db.Column(db.String(15))
    activo = db.Column(db.Boolean, default=True)
    distribuidores = db.relationship('DimDistribuidor', back_populates='grupo', cascade='all, delete-orphan', lazy=True)

# --- Distribuidor normalizado ---
class DimDistribuidor(db.Model):
    __tablename__ = 'Dim_Distribuidor'
    id_distribuidor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo_distribuidor = db.Column(db.String(20), unique=True, nullable=False)
    nombre_distribuidor = db.Column(db.String(255), nullable=False)
    cupo_asignado = db.Column(db.Numeric(15,2), default=0.00)
    id_municipio = db.Column(db.String(5), db.ForeignKey('Dim_Municipio.id_municipio'))
    activo = db.Column(db.Boolean, default=True)
    id_grupo = db.Column(db.Integer, db.ForeignKey('Dim_GrupoDistribuidor.id_grupo'), nullable=True)
    grupo = db.relationship('DimGrupoDistribuidor', back_populates='distribuidores')
    ventas = db.relationship('FactVentas', back_populates='distribuidor', lazy=True)


class DimTiempo(db.Model):
    __tablename__ = 'Dim_Tiempo'
    id_tiempo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha = db.Column(db.Date, unique=True, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    dia = db.Column(db.Integer, nullable=False)
    dia_semana_nombre = db.Column(db.String(20))
    dia_semana_num = db.Column(db.Integer)
    es_fin_semana = db.Column(db.Boolean)
    trimestre = db.Column(db.Integer)

# --- Hechos de Ventas ---
class FactVentas(db.Model):
    __tablename__ = 'Fact_Ventas'
    id_venta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_tiempo = db.Column(db.Integer, db.ForeignKey('Dim_Tiempo.id_tiempo'), nullable=False)
    id_distribuidor = db.Column(db.Integer, db.ForeignKey('Dim_Distribuidor.id_distribuidor'), nullable=False)
    id_municipio = db.Column(db.String(5), db.ForeignKey('Dim_Municipio.id_municipio'), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    fecha_carga = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sorteo = db.Column(db.Integer, nullable=False)
    cantidad_despachada = db.Column(db.Integer, default=0)
    cantidad_devuelta = db.Column(db.Integer, default=0)
    cantidad_vendida = db.Column(db.Integer, default=0)
    bruto_despacho = db.Column(db.Numeric(15,2), default=0.00)
    bruto_devuelto = db.Column(db.Numeric(15,2), default=0.00)
    bruto_vendido = db.Column(db.Numeric(15,2), default=0.00)
    neto_vendido = db.Column(db.Numeric(15,2), default=0.00)
    porcentaje_comision = db.Column(db.Numeric(5,2))
    distribuidor = db.relationship('DimDistribuidor', back_populates='ventas')

