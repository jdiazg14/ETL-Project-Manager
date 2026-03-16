"""Formularios para autenticación"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import Users


class RegistroForm(FlaskForm):
    """Formulario de registro de usuario."""
    
    username = StringField(
        'Usuario',
        validators=[
            DataRequired(),
            Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
        ]
    )
    
    email = StringField(
        'Correo Electrónico',
        validators=[
            DataRequired(),
            Email(message='Ingrese un correo electrónico válido')
        ]
    )
    
    first_name = StringField('Nombre')
    last_name = StringField('Apellido')
    
    password = PasswordField(
        'Contraseña',
        validators=[
            DataRequired(),
            Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
        ]
    )
    
    confirm_password = PasswordField(
        'Confirmar Contraseña',
        validators=[
            DataRequired(),
            EqualTo('password', message='Las contraseñas no coinciden')
        ]
    )
    
    submit = SubmitField('Registrarse')
    
    def validate_username(self, field):
        """Validar que el username no exista."""
        if Users.query.filter_by(username=field.data).first():
            raise ValidationError('El usuario ya existe.')
    
    def validate_email(self, field):
        """Validar que el email no exista."""
        if Users.query.filter_by(email=field.data).first():
            raise ValidationError('El correo ya está registrado.')


class LoginForm(FlaskForm):
    """Formulario de login."""
    
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')
