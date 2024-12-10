from flask import Blueprint, jsonify, render_template, send_file, session, redirect, url_for, flash, request
from datetime import datetime, timedelta
from io import BytesIO 
from openpyxl import Workbook 
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

@main_bp.route("/ventas", methods=['GET'])
def ventas():
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Obtener productos y ventas
            cursor.execute("SELECT * FROM productos")
            productos = cursor.fetchall()

            cursor.execute("""
                SELECT V.id_venta, V.fecha, P.nombre AS producto, DV.id_detalle, DV.cantidad, 
                       DV.precio_unitario, DV.subtotal 
                FROM ventas V
                JOIN detalle_ventas DV ON V.id_venta = DV.id_venta
                JOIN productos P ON DV.id_producto = P.id_producto
                ORDER BY V.fecha DESC
            """)
            ventas = cursor.fetchall()

            return render_template("ventas.html", productos=productos, ventas=ventas)
    except mysql.connector.Error as err:
        flash("Error al gestionar ventas.", "danger")
        return redirect(url_for('main.dashboard'))

@main_bp.route("/ventas/registrar", methods=['GET', 'POST'])
def registrar_venta():
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                id_producto = request.form['producto']
                cantidad = int(request.form['cantidad'])
                id_usuario = session['user_id']

                # Verificar producto y stock
                cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id_producto,))
                producto = cursor.fetchone()
                if not producto:
                    flash("El producto no existe.", "danger")
                    return redirect(url_for('main.registrar_venta'))
                if producto['stock'] < cantidad:
                    flash("Stock insuficiente para este producto.", "warning")
                    return redirect(url_for('main.registrar_venta'))

                # Calcular subtotal
                precio_unitario = producto['precio']
                subtotal = precio_unitario * cantidad

                # Insertar la venta y su detalle
                cursor.execute("INSERT INTO ventas (id_usuario, total_venta) VALUES (%s, %s)", 
                               (id_usuario, subtotal))
                id_venta = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_venta, id_producto, cantidad, precio_unitario, subtotal))

                # Actualizar stock
                cursor.execute("UPDATE productos SET stock = stock - %s WHERE id_producto = %s", 
                               (cantidad, id_producto))
                conn.commit()
                flash("Venta registrada con éxito.", "success")
                return redirect(url_for('main.ventas'))

        except mysql.connector.Error as err:
            flash("Error al registrar la venta.", "danger")
            return redirect(url_for('main.ventas'))

    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM productos")
            productos = cursor.fetchall()
            return render_template("ventas_registrar.html", productos=productos)
    except mysql.connector.Error as err:
        flash("Error al cargar productos.", "danger")
        return redirect(url_for('main.ventas'))

@main_bp.route("/ventas/editar/<int:id_detalle>", methods=['GET', 'POST'])
def editar_venta(id_detalle):
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                nueva_cantidad = int(request.form['nueva_cantidad'])

                # Obtener detalles actuales
                cursor.execute("SELECT * FROM detalle_ventas WHERE id_detalle = %s", (id_detalle,))
                detalle_actual = cursor.fetchone()
                if not detalle_actual:
                    flash("El detalle de la venta no existe.", "danger")
                    return redirect(url_for('main.ventas'))

                # Verificar nuevo stock
                id_producto = detalle_actual['id_producto']
                cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id_producto,))
                producto = cursor.fetchone()
                stock_disponible = producto['stock'] + detalle_actual['cantidad']
                if nueva_cantidad > stock_disponible:
                    flash("Stock insuficiente para la nueva cantidad.", "warning")
                    return redirect(url_for('main.ventas'))

                # Actualizar el detalle y el stock
                nuevo_subtotal = producto['precio'] * nueva_cantidad
                cursor.execute("""
                    UPDATE detalle_ventas 
                    SET cantidad = %s, subtotal = %s 
                    WHERE id_detalle = %s
                """, (nueva_cantidad, nuevo_subtotal, id_detalle))
                cursor.execute("UPDATE productos SET stock = stock + %s - %s WHERE id_producto = %s", 
                               (detalle_actual['cantidad'], nueva_cantidad, id_producto))
                conn.commit()
                flash("Venta actualizada con éxito.", "success")
                return redirect(url_for('main.ventas'))

        except mysql.connector.Error as err:
            flash("Error al actualizar la venta.", "danger")
            return redirect(url_for('main.ventas'))

    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DV.*, P.nombre AS producto, P.precio AS precio_unitario 
                FROM detalle_ventas DV
                JOIN productos P ON DV.id_producto = P.id_producto
                WHERE DV.id_detalle = %s
            """, (id_detalle,))
            detalle = cursor.fetchone()
            if not detalle:
                flash("El detalle de la venta no existe.", "danger")
                return redirect(url_for('main.ventas'))

            return render_template("ventas_editar.html", detalle=detalle)
    except mysql.connector.Error as err:
        flash("Error al cargar detalles.", "danger")
        return redirect(url_for('main.ventas'))

@main_bp.route("/ventas/eliminar/<int:id_venta>", methods=['POST'])
def eliminar_venta(id_venta):
    if 'user_id' not in session:
        flash("Debes iniciar sesión primero.", "danger")
        return redirect(url_for('auth.login'))

    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Obtener detalles de la venta
            cursor.execute("SELECT * FROM detalle_ventas WHERE id_venta = %s", (id_venta,))
            detalles = cursor.fetchall()

            # Restaurar el stock
            for detalle in detalles:
                cursor.execute("UPDATE productos SET stock = stock + %s WHERE id_producto = %s", 
                               (detalle['cantidad'], detalle['id_producto']))

            # Eliminar detalles y la venta
            cursor.execute("DELETE FROM detalle_ventas WHERE id_venta = %s", (id_venta,))
            cursor.execute("DELETE FROM ventas WHERE id_venta = %s", (id_venta,))
            conn.commit()
            flash("Venta eliminada con éxito.", "success")
            return redirect(url_for('main.ventas'))
    except mysql.connector.Error as err:
        flash("Error al eliminar la venta.", "danger")
        return redirect(url_for('main.ventas'))

# Ruta para la página de reportes
@main_bp.route("/reportes", methods=["GET", "POST"])
def reportes():
    if request.method == "POST":
        filtro = request.json.get("filtro", "mes")  # Predeterminado a "mes"
        hoy = datetime.now()

        if filtro == "semana":
            inicio = hoy - timedelta(days=hoy.weekday())
        elif filtro == "mes":
            inicio = hoy.replace(day=1)
        elif filtro == "año":
            inicio = hoy.replace(month=1, day=1)
        else:
            inicio = hoy  # Default: sin filtro

        try:
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Consultar las ventas filtradas
                cursor.execute("""
                    SELECT SUM(V.total_venta) as total_ventas, COUNT(V.id_venta) as num_ventas
                    FROM Ventas V
                    WHERE V.fecha >= %s
                """, (inicio,))
                stats = cursor.fetchone()

                # Producto más vendido
                cursor.execute("""
                    SELECT P.nombre, SUM(DV.cantidad) as total_vendido
                    FROM Detalle_Ventas DV
                    JOIN Productos P ON P.id_producto = DV.id_producto
                    WHERE DV.id_venta IN (SELECT id_venta FROM Ventas WHERE fecha >= %s)
                    GROUP BY P.nombre
                    ORDER BY total_vendido DESC
                    LIMIT 1
                """, (inicio,))
                producto_mas_vendido = cursor.fetchone()

            return jsonify({
                "total_ventas": stats['total_ventas'],
                "num_ventas": stats['num_ventas'],
                "producto_mas_vendido": producto_mas_vendido['nombre'] if producto_mas_vendido else "N/A"
            })

        except mysql.connector.Error as err:
            return jsonify({"error": str(err)}), 500

    return render_template("reportes.html")


# Ruta para exportar a Excel
@main_bp.route("/exportar/excel", methods=["GET"])
def exportar_excel():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_venta, fecha, total_venta FROM Ventas
        """)
        ventas = cursor.fetchall()

        # Crear un archivo Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Ventas"

        # Escribir encabezados
        ws.append(["ID Venta", "Fecha", "Total Venta"])

        # Escribir datos de ventas
        for venta in ventas:
            ws.append([venta["id_venta"], venta["fecha"], venta["total_venta"]])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, attachment_filename="reportes_ventas.xlsx", as_attachment=True)

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500