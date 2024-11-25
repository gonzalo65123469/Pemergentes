from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import mysql.connector
from functools import wraps
from ..models import get_connection

# Crear un blueprint para la autenticación
auth_bp = Blueprint('auth', __name__)

# Tiempo de expiración de la sesión
SESSION_TIMEOUT = timedelta(minutes=30)

# Decorador para autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Debe iniciar sesión para acceder a esta página.", "warning")
            return redirect(url_for('auth.login'))

        # Verificar tiempo de inactividad
        last_active = datetime.fromisoformat(session.get('last_active'))
        if datetime.now() - last_active > SESSION_TIMEOUT:
            session.clear()
            flash("Su sesión ha expirado. Por favor, inicie sesión nuevamente.", "warning")
            return redirect(url_for('auth.login'))

        # Actualizar el tiempo de última actividad
        session['last_active'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

# Ruta para registrar usuarios
@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        correo = request.form['correo']
        password = request.form['password']
        password_encriptado = generate_password_hash(password)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Usuarios (nombre_usuario, correo, contraseña) VALUES (%s, %s, %s)",
                           (nombre_usuario, correo, password_encriptado))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Usuario registrado con éxito.", "success")
            return redirect(url_for('auth.login'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
            return redirect(url_for('auth.register'))
    return render_template("auth/register.html")

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        password = request.form['password']

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Usuarios WHERE nombre_usuario = %s", (nombre_usuario,))
            usuario = cursor.fetchone()
            conn.close()

            if not usuario:
                flash("Usuario no registrado.", "danger")
            elif not check_password_hash(usuario['contraseña'], password):
                flash("Contraseña incorrecta.", "danger")
            else:
                session['user_id'] = usuario['id_usuario']
                session['username'] = usuario['nombre_usuario']
                session['last_active'] = datetime.now().isoformat()
                flash("Inicio de sesión exitoso.", "success")
                return redirect(url_for('main.dashboard'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
    return render_template('auth/login.html')

# Ruta para el logout
@auth_bp.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Has cerrado sesión.", "success")
    return redirect(url_for('auth.login'))
