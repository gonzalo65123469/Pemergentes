from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import mysql.connector
from ..models import get_connection
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/admin/dashboard")
def dashboard():
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")  
        return redirect(url_for('auth.login'))
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT nombre, stock 
            FROM Productos 
            WHERE stock <= 5 
            ORDER BY stock ASC;
        """)
        productos_bajo_stock = cursor.fetchall()
        cursor.execute("""
            SELECT P.nombre, DV.cantidad 
            FROM Ventas V 
            JOIN Detalle_Ventas DV ON V.id_venta = DV.id_venta 
            JOIN Productos P ON DV.id_producto = P.id_producto 
            ORDER BY V.fecha DESC 
            LIMIT 5;
        """)
        ventas_recientes = cursor.fetchall()
        cursor.execute("""
            SELECT P.nombre, SUM(DV.cantidad) AS total_vendido 
            FROM Detalle_Ventas DV 
            JOIN Productos P ON DV.id_producto = P.id_producto 
            GROUP BY P.nombre 
            ORDER BY total_vendido DESC 
            LIMIT 5;
        """)
        productos_mas_vendidos = cursor.fetchall()
        conn.close()
        return render_template("admin/dashboard.html", 
                               productos_bajo_stock=productos_bajo_stock,
                               ventas_recientes=ventas_recientes,
                               productos_mas_vendidos=productos_mas_vendidos)
    except mysql.connector.Error as err:
        flash(f"Error al obtener datos: {err}", "danger")
        return redirect(url_for('main.index'))
    
@main_bp.route("/productos", methods=['GET', 'POST'])
def productos():
    
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if request.method == 'POST':
            busqueda = request.form['buscar']
            query = "SELECT * FROM Productos WHERE nombre LIKE %s"
            cursor.execute(query, ('%' + busqueda + '%',))
        else:
            cursor.execute("SELECT * FROM Productos")
        productos = cursor.fetchall()
        conn.close()
        return render_template("productos.html", productos=productos)
    except mysql.connector.Error as err:  
        flash(f"Error al obtener datos: {err}", "danger")
        return redirect(url_for('main.dashboard'))
    
@main_bp.route("/productos/agregar", methods=['GET', 'POST'])
def agregar_producto():
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        nombre = request.form['nombre']  
        categoria = request.form['categoria'] 
        precio = request.form['precio']  # Obtener el precio del producto del formulario
        stock = request.form['stock']  # Obtener el stock del producto del formulario
        descripcion = request.form['descripcion']  # Obtener la descripción del producto del formulario
        try:
            # Obtener la conexión a la base de datos
            conn = get_connection()
            # Crear un cursor para ejecutar comandos SQL
            cursor = conn.cursor()
            # Ejecutar el comando SQL para insertar un nuevo producto
            cursor.execute("INSERT INTO Productos (nombre, categoria, precio, stock, descripcion) VALUES (%s, %s, %s, %s, %s)",
                           (nombre, categoria, precio, stock, descripcion))
            # Confirmar la transacción
            conn.commit()
            # Cerrar el cursor
            cursor.close()
            # Cerrar la conexión a la base de datos
            conn.close()
            # Mostrar un mensaje de éxito al usuario
            flash("Producto agregado con éxito.", "success")
            # Redirigir a la página de productos
            return redirect(url_for('main.productos'))
        except mysql.connector.Error as err:  # Manejar errores de MySQL
            # Mostrar un mensaje de error al usuario
            flash(f"Error: {err}", "danger")
            # Redirigir a la página de agregar producto
            return redirect(url_for('main.agregar_producto'))
    # Renderizar la plantilla para agregar un nuevo producto
    return render_template("productos_agregar.html")

# Ruta para editar un producto existente
@main_bp.route("/productos/editar/<int:id_producto>", methods=['GET', 'POST'])
def editar_producto(id_producto):
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            nombre = request.form['nombre']
            categoria = request.form['categoria']
            precio = request.form['precio']
            stock = request.form['stock']
            descripcion = request.form['descripcion']

            cursor.execute("UPDATE Productos SET nombre=%s, categoria=%s, precio=%s, stock=%s, descripcion=%s WHERE id_producto=%s",
                           (nombre, categoria, precio, stock, descripcion, id_producto))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Producto actualizado con éxito.", "success")
            return redirect(url_for('main.productos'))

        cursor.execute("SELECT * FROM Productos WHERE id_producto = %s", (id_producto,))
        producto = cursor.fetchone()
        conn.close()
        return render_template("productos_editar.html", producto=producto)
    except mysql.connector.Error as err:
        flash(f"Error al obtener datos: {err}", "danger")
        return redirect(url_for('main.productos'))

# Ruta para eliminar un producto
@main_bp.route("/productos/eliminar/<int:id_producto>", methods=['POST'])
def eliminar_producto(id_producto):
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Productos WHERE id_producto = %s", (id_producto,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Producto eliminado con éxito.", "success")
        return redirect(url_for('main.productos'))
    except mysql.connector.Error as err:
        flash(f"Error al eliminar el producto: {err}", "danger")
        return redirect(url_for('main.productos'))
    
# Ruta para registrar una venta
@main_bp.route("/ventas/registrar", methods=['GET', 'POST'])
def registrar_venta():
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        id_producto = request.form['producto']
        cantidad = int(request.form['cantidad'])

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Obtener detalles del producto
            cursor.execute("SELECT * FROM Productos WHERE id_producto = %s", (id_producto,))
            producto = cursor.fetchone()
            if not producto:
                flash("Producto no encontrado.", "danger")
                return redirect(url_for('main.registrar_venta'))

            precio_unitario = producto['precio']
            subtotal = precio_unitario * cantidad

            # Insertar la venta en la tabla Ventas
            cursor.execute("INSERT INTO Ventas (id_usuario, total_venta) VALUES (%s, %s)", (session['user_id'], subtotal))
            id_venta = cursor.lastrowid

            # Insertar el detalle de la venta
            cursor.execute("INSERT INTO Detalle_Ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                           (id_venta, id_producto, cantidad, precio_unitario, subtotal))
            
            # Actualizar el stock del producto
            cursor.execute("UPDATE Productos SET stock = stock - %s WHERE id_producto = %s", (cantidad, id_producto))
            
            conn.commit()
            cursor.close()
            conn.close()
            flash("Producto agregado a la venta con éxito.", "success")
            return redirect(url_for('main.registrar_venta'))

        except mysql.connector.Error as err:
            flash(f"Error: {err}", "danger")
            return redirect(url_for('main.registrar_venta'))

    # Obtener la lista de productos para el formulario
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_producto, nombre FROM Productos")
        productos = cursor.fetchall()
        conn.close()
        return render_template("ventas_registrar.html", productos=productos)
    except mysql.connector.Error as err:
        flash(f"Error al obtener datos: {err}", "danger")
        return redirect(url_for('main.dashboard'))
    
# Ruta para editar una venta
@main_bp.route("/ventas/editar/<int:id_venta>", methods=['GET', 'POST'])
def editar_venta(id_venta):
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            id_producto = request.form['producto']
            cantidad = int(request.form['cantidad'])

            # Obtener detalles del producto
            cursor.execute("SELECT * FROM Productos WHERE id_producto = %s", (id_producto,))
            producto = cursor.fetchone()
            if not producto:
                flash("Producto no encontrado.", "danger")
                return redirect(url_for('main.editar_venta', id_venta=id_venta))

            precio_unitario = producto['precio']
            subtotal = precio_unitario * cantidad

            # Actualizar la venta en la tabla Ventas
            cursor.execute("UPDATE Ventas SET total_venta = %s WHERE id_venta = %s", (subtotal, id_venta))

            # Actualizar el detalle de la venta
            cursor.execute("UPDATE Detalle_Ventas SET id_producto = %s, cantidad = %s, precio_unitario = %s, subtotal = %s WHERE id_venta = %s",
                           (id_producto, cantidad, precio_unitario, subtotal, id_venta))

            conn.commit()
            cursor.close()
            conn.close()
            flash("Venta actualizada con éxito.", "success")
            return redirect(url_for('main.listado_ventas'))

        cursor.execute("SELECT * FROM Ventas V JOIN Detalle_Ventas DV ON V.id_venta = DV.id_venta WHERE V.id_venta = %s", (id_venta,))
        venta = cursor.fetchone()
        cursor.execute("SELECT id_producto, nombre FROM Productos")
        productos = cursor.fetchall()
        conn.close()
        return render_template("ventas_editar.html", venta=venta, productos=productos)
    except mysql.connector.Error as err:
        flash(f"Error al obtener datos: {err}", "danger")
        return redirect(url_for('main.listado_ventas'))

    
# Ruta para eliminar una venta
@main_bp.route("/ventas/eliminar/<int:id_venta>", methods=['POST'])
def eliminar_venta(id_venta):
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener el detalle de la venta para ajustar el stock del producto
        cursor.execute("SELECT id_producto, cantidad FROM Detalle_Ventas WHERE id_venta = %s", (id_venta,))
        detalle_venta = cursor.fetchone()
        id_producto = detalle_venta[0]  # Acceder a los elementos de la tupla con índices enteros
        cantidad = detalle_venta[1]  # Acceder a los elementos de la tupla con índices enteros

        # Actualizar el stock del producto
        cursor.execute("UPDATE Productos SET stock = stock + %s WHERE id_producto = %s", (cantidad, id_producto))

        # Eliminar el detalle de la venta
        cursor.execute("DELETE FROM Detalle_Ventas WHERE id_venta = %s", (id_venta,))
        
        # Eliminar la venta
        cursor.execute("DELETE FROM Ventas WHERE id_venta = %s", (id_venta,))

        conn.commit()
        cursor.close()
        conn.close()
        flash("Venta eliminada con éxito.", "success")
        return redirect(url_for('main.listado_ventas'))
    except mysql.connector.Error as err:
        flash(f"Error al eliminar la venta: {err}", "danger")
        return redirect(url_for('main.listado_ventas'))



# Ruta para listar ventas
@main_bp.route("/ventas", methods=['GET'])
def listado_ventas():
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT V.id_venta, P.nombre AS nombre_producto, DV.cantidad, DV.precio_unitario, DV.subtotal 
            FROM Ventas V 
            JOIN Detalle_Ventas DV ON V.id_venta = DV.id_venta 
            JOIN Productos P ON DV.id_producto = P.id_producto
        """)
        ventas = cursor.fetchall()
        conn.close()
        return render_template("ventas.html", ventas=ventas)
    except mysql.connector.Error as err:
        flash(f"Error al obtener datos: {err}", "danger")
        return redirect(url_for('main.dashboard'))
