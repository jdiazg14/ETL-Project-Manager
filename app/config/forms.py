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
    is_active = BooleanField('Activo', default=True)
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


# --- Formulario para Grupos ---
from app.models import DimGrupoDistribuidor, DimDepartamento, DimMunicipio

class GrupoForm(FlaskForm):
    nombre_grupo = StringField('Nombre del Grupo', validators=[DataRequired()])
    nit = StringField('NIT', validators=[DataRequired()])
    plan = StringField('Plan')
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')

# --- Formularios para Distribuidores ---
class DistribuidorForm(FlaskForm):
    codigo_distribuidor = StringField('Código Distribuidor', validators=[DataRequired()])
    nombre_distribuidor = StringField('Nombre Distribuidor', validators=[DataRequired()])
    cupo_asignado = StringField('Cupo Asignado')
    id_grupo = SelectField('Grupo', coerce=lambda x: int(x) if x not in (None, '', 0) and (isinstance(x, int) or (isinstance(x, str) and x.isdigit())) else None, validators=[Optional()])
    id_departamento = SelectField('Departamento', coerce=str, validators=[DataRequired()])
    id_municipio = SelectField('Municipio', coerce=str, validators=[DataRequired()])
    activo = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        grupos = [(g.id_grupo, g.nombre_grupo) for g in DimGrupoDistribuidor.query.order_by(DimGrupoDistribuidor.nombre_grupo).all()]
        self.id_grupo.choices = [('', '-- Sin Grupo --')] + grupos
        self.id_departamento.choices = [(d.id_departamento, d.nombre_depto) for d in DimDepartamento.query.order_by(DimDepartamento.nombre_depto).all()]
        # Municipios se cargan dinámicamente por JS, pero si hay un departamento seleccionado, cargar municipios
        if self.id_departamento.data:
            self.id_municipio.choices = [(m.id_municipio, m.nombre_municipio) for m in DimMunicipio.query.filter_by(id_departamento=self.id_departamento.data).order_by(DimMunicipio.nombre_municipio).all()]
        else:
            self.id_municipio.choices = []
