# app/models.py
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='Tienda'
    )

def init_mysql_db():
    try:
        conn = get_connection()
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Usuarios (
                    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
                    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
                    correo VARCHAR(100) NOT NULL UNIQUE,
                    contraseña VARCHAR(255) NOT NULL,
                    rol ENUM('admin', 'usuario') DEFAULT 'usuario'
                )
                """
            )
            conn.commit()
            cursor.close()
            conn.close()
            print("Base de datos y tabla de usuarios creadas exitosamente.")
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos MySQL: {err}")

init_mysql_db()
