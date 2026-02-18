from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo
from app.models import User, Role

class UsuarioForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir')])
    role_id = SelectField('Rol', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Activo')
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
        analista_role = Role.query.filter((Role.name == 'analista') | (Role.name == 'Analista')).first()
        if analista_role:
            self.role_id.default = analista_role.id
        self.is_active.default = True
        self.process()
