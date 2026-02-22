from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Optional
from app.models import Users, Role

class UsuarioForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[Optional()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[Optional(), EqualTo('password', message='Las contraseñas deben coincidir')])
    role_id = SelectField('Rol', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Activo')
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
        analista_role = Role.query.filter((Role.name == 'analista') | (Role.name == 'Analista')).first()
        if analista_role and not self.role_id.data:
            self.role_id.data = analista_role.id
        if self.is_active.data is None:
            self.is_active.data = True
        
# --- Formularios para Departamentos ---
class DepartamentoForm(FlaskForm):
    id_departamento = StringField('Código Departamento', validators=[DataRequired()])
    nombre_depto = StringField('Nombre Departamento', validators=[DataRequired()])
    submit = SubmitField('Guardar')

# --- Formularios para Municipios ---
class MunicipioForm(FlaskForm):
    id_municipio = StringField('Código Municipio', validators=[DataRequired()])
    id_departamento = SelectField('Departamento', validators=[DataRequired()], coerce=str)
    nombre_municipio = StringField('Nombre Municipio', validators=[DataRequired()])
    submit = SubmitField('Guardar')

# --- Formularios para Distribuidores ---
class DistribuidorForm(FlaskForm):
    codigo_sucursal = StringField('Código Sucursal', validators=[DataRequired()])
    nombre_sucursal = StringField('Nombre Sucursal', validators=[DataRequired()])
    nit = StringField('NIT', validators=[DataRequired()])
    razon_social = StringField('Razón Social')
    cupo_asignado = StringField('Cupo Asignado')
    grupo = StringField('Grupo')
    id_municipio = SelectField('Municipio', validators=[DataRequired()], coerce=str)
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')
