from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class RoleForm(FlaskForm):
    name = StringField('Nombre del Rol', validators=[DataRequired()])
    description = TextAreaField('Descripción')
    submit = SubmitField('Guardar')
