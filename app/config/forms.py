from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email
from app.models import User, Role

class UsuarioForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    first_name = StringField('Nombre')
    last_name = StringField('Apellido')
    role_id = SelectField('Rol', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Activo')
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
