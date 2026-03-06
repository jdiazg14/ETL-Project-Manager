from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.models import db, DimGrupoDistribuidor
from app.config.forms import GrupoForm
from app.config.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates/admin')

@admin_bp.route('/grupos')
@login_required
@admin_required
def grupos_index():
    grupos = DimGrupoDistribuidor.query.order_by(DimGrupoDistribuidor.nombre_grupo).all()
    return render_template('grupos.html', grupos=grupos)

@admin_bp.route('/grupos/nuevo', methods=['GET', 'POST'])
@login_required
@admin_required
def nuevo_grupo():
    form = GrupoForm()
    if form.validate_on_submit():
        grupo = DimGrupoDistribuidor(nombre_grupo=form.nombre_grupo.data)
        db.session.add(grupo)
        db.session.commit()
        flash('Grupo creado correctamente.', 'success')
        return redirect(url_for('admin.grupos_index'))
    return render_template('grupo_form.html', form=form, crear=True)
