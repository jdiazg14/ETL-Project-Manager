"""
Modelos de base de datos según schema.sql
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

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
    logs = db.relationship('ETLProjectLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role and self.role.name == 'admin'

    def __repr__(self):
        return f'<Users {self.username}>'

class ETLProjectLog(db.Model):
    __tablename__ = 'etl_project_logs'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ETLProjectLog {self.filename}>'

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

class DimDistribuidor(db.Model):
    __tablename__ = 'Dim_Distribuidor'
    id_distribuidor = db.Column(db.Integer, primary_key=True)
    codigo_sucursal = db.Column(db.String(20), unique=True, nullable=False)
    nombre_sucursal = db.Column(db.String(255), nullable=False)
    nit = db.Column(db.String(20), nullable=False)
    razon_social = db.Column(db.String(255))
    cupo_asignado = db.Column(db.Numeric(15,2), default=0.00)
    grupo = db.Column(db.String(50))
    id_municipio = db.Column(db.String(5), db.ForeignKey('Dim_Municipio.id_municipio'))
    activo = db.Column(db.Boolean, default=True)

