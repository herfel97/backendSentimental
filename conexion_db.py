import mysql.connector

class ConexionBD:
    def __init__(self):
        self.conexion = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="sentimientos",
            password="sentimientos",
            database="sentimientos_db"
        )
        self.cursor = self.conexion.cursor()

    def verificar_conexion(self):
        if not self.conexion.is_connected():
            # print("Reconectando con la basede datos .... ")
            self.conexion.connect()
            
    def ejecutar_consulta(self, consulta, valores=None):
        self.verificar_conexion()
        self.cursor.execute(consulta, valores)
        if 'SELECT' in consulta:
            return self.cursor.fetchall()
        else:
            self.conexion.commit()
            return self.cursor.lastrowid

    def cerrar_conexion(self):
        self.cursor.close()
        self.conexion.close()

    # def guardar_usuario(id_usuario, usuario_coment_extraido, residencia_usuario, sexo_usuario, fecha_nac_usuario):
    #     self