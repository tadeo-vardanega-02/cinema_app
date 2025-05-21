from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Usuario, Hilo, Comentario
from config import Config
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from markupsafe import Markup
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.template_filter('nl2br')
def nl2br_filter(s):
    if s is None:
        return ''
    return Markup(s.replace('\n', '<br>'))

# --- Formularios ---

class RegistroForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(1,64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(6,128)])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        if Usuario.query.filter_by(username=username.data).first():
            raise ValidationError('El nombre de usuario ya está en uso.')

    def validate_email(self, email):
        if Usuario.query.filter_by(email=email.data).first():
            raise ValidationError('El email ya está registrado.')

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')

class HiloForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired(), Length(max=140)])
    contenido = TextAreaField('Contenido', validators=[DataRequired()])
    submit = SubmitField('Crear Hilo')

class ComentarioForm(FlaskForm):
    contenido = TextAreaField('Comentario', validators=[DataRequired()])
    submit = SubmitField('Comentar')

# --- Login Manager ---

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- Rutas ---

@app.route('/')
def index():
    hilos = Hilo.query.order_by(Hilo.fecha_creacion.desc()).all()
    return render_template('index.html', hilos=hilos)

@app.route('/registro', methods=['GET','POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistroForm()
    if form.validate_on_submit():
        usuario = Usuario(username=form.username.data, email=form.email.data)
        usuario.set_password(form.password.data)
        db.session.add(usuario)
        db.session.commit()
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(username=form.username.data).first()
        if usuario and usuario.check_password(form.password.data):
            login_user(usuario)
            flash('Has iniciado sesión correctamente.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

@app.route('/crear_hilo', methods=['GET','POST'])
@login_required
def crear_hilo():
    form = HiloForm()
    if form.validate_on_submit():
        hilo = Hilo(titulo=form.titulo.data, contenido=form.contenido.data, autor=current_user)
        db.session.add(hilo)
        db.session.commit()
        flash('Hilo creado correctamente.', 'success')
        return redirect(url_for('index'))
    return render_template('crear_hilo.html', form=form)

@app.route('/hilo/<int:hilo_id>', methods=['GET', 'POST'])
def hilo(hilo_id):
    hilo = Hilo.query.get_or_404(hilo_id)
    form = ComentarioForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Debes estar logueado para comentar.', 'warning')
            return redirect(url_for('login'))
        comentario = Comentario(contenido=form.contenido.data, autor=current_user, hilo=hilo)
        db.session.add(comentario)
        db.session.commit()
        flash('Comentario agregado.', 'success')
        return redirect(url_for('hilo', hilo_id=hilo_id))
    comentarios = hilo.comentarios.order_by(Comentario.fecha_creacion.asc()).all()
    return render_template('hilo.html', hilo=hilo, comentarios=comentarios, form=form)

# Ruta para agregar comentario vía AJAX
@app.route('/comentario_ajax/<int:hilo_id>', methods=['POST'])
@login_required
def comentario_ajax(hilo_id):
    data = request.get_json()
    contenido = data.get('contenido', '')
    if not contenido.strip():
        return jsonify({'error': 'El comentario no puede estar vacío.'}), 400
    hilo = Hilo.query.get_or_404(hilo_id)
    comentario = Comentario(contenido=contenido, autor=current_user, hilo=hilo)
    db.session.add(comentario)
    db.session.commit()
    # Devolver datos para agregar comentario en frontend sin recargar
    return jsonify({
        'usuario': current_user.username,
        'contenido': comentario.contenido,
        'fecha': comentario.fecha_creacion.strftime('%Y-%m-%d %H:%M')
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

