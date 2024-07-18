from conexion_db import ConexionBD
from datetime import datetime, timedelta

import mysql.connector.errors

class controlador_bd():
    
    def __init__(self):
        self.bd = ConexionBD()
  
    def convertir_fecha(self, fecha_str):  
        if 'Ayer' in fecha_str:
            fecha_actual = datetime.now()
            fecha_anterior = fecha_actual - timedelta(days=1)
            return fecha_anterior.date()
        elif 'dia' in fecha_str:
            fecha_actual = datetime.now()
            # fecha_anterior = fecha_actual - timedelta(days=)
            # fecha_formato = fecha_anterior.strftime("%d %m %Y")
        elif 'sem' in fecha_str:
            print()
        elif 'hora' in fecha_str or 'h' in fecha_str:
            return datetime.now().date()
        elif 'min' in fecha_str:
            return datetime.now().date()
        elif 'Hoy' in fecha_str:
            return datetime.now().date()
        elif 'momento' in fecha_str:
            return datetime.now().date()    
        elif fecha_str:
            meses_espanol = {'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12,}
            meses_abr = {'ene.': 1, 'feb.': 2, 'mar.': 3, 'abr.': 4, 'may.': 5, 'jun.': 6, 'jul.': 7, 'ago.': 8, 'sep.': 9, 'oct.': 10, 'nov.': 11, 'dic.': 12,}
            dias_semana = {'lunes': 0, 'martes': 1, 'miércoles': 2, 'jueves': 3, 'viernes': 4, 'sábado': 5, 'domingo': 6}
            partes_fecha = fecha_str.split()
            
            if partes_fecha[0] in dias_semana:
                dia_semana_numero = dias_semana[partes_fecha[0].lower()]
                fecha_actual = datetime.now()
                fecha_ajustada = fecha_actual - timedelta(days=(fecha_actual.weekday() - dia_semana_numero) % 7)
                return fecha_ajustada.date()
            
            if not 'de' in fecha_str:
                mes = partes_fecha[1]
                numero_mes = meses_abr[mes]
                fecha_formato = f"{partes_fecha[0]} {numero_mes} {partes_fecha[2]}"
            elif len(partes_fecha) > 3:
                mes = partes_fecha[2]
                if '.' in mes:
                    numero_mes = meses_abr[mes]
                else: 
                    numero_mes = meses_espanol[mes.capitalize()]
                if not 'las' in partes_fecha[4]:
                    fecha_formato = f"{partes_fecha[0]} {numero_mes} {partes_fecha[4]}"
                else:
                    fecha_formato = f"{partes_fecha[0]} {numero_mes} {datetime.now().year}"
            elif len(partes_fecha) == 3:
                mes = partes_fecha[2]
                if '.' in mes:
                    numero_mes = meses_abr[mes]
                    fecha_formato = f"{partes_fecha[0]} {numero_mes} {datetime.now().year}"
                else: 
                    numero_mes = meses_espanol[mes.capitalize()]
                    fecha_formato = f"{partes_fecha[0]} {numero_mes}"
        else:
            return None
            
        fecha = fecha_formato.split()
        if len(fecha) == 3:
            fecha_obj = datetime.strptime(fecha_formato, "%d %m %Y") 
        else:
            fecha_obj = datetime.strptime(fecha_formato, "%d %m")
            
        fecha_nac_usuario = fecha_obj.date() if fecha_obj else None
        
        return fecha_nac_usuario

    def guardarUsuario(self, id_usuario, usuario_coment_extraido, extraido, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion):

        try:
            consulta = "INSERT INTO usuario (us_id_usuario, us_url, us_extraido, us_residencia, us_sexo, us_fecha_nacimiento) VALUES (%s, %s, %s, %s, %s, %s)"
            valores = (id_usuario, usuario_coment_extraido, extraido, residencia_usuario, sexo_usuario, self.convertir_fecha(fecha_nac_usuario) )
            usuario = False
            id_usuario = self.bd.ejecutar_consulta(consulta = consulta, valores = valores)

            if len( list_educacion ) > 0 and not usuario:
                for i in list_educacion:        
                    consultaEducacion = "INSERT INTO formacion_academica (form_acd_estudio, form_ac_us_id) VALUES (%s, %s)"
                    valoresEducacion = (i, id_usuario)
                    self.bd.ejecutar_consulta(consulta = consultaEducacion, valores = valoresEducacion)      
        
        except Exception as e:
            if e.errno == 1062 and not extraido:
                id_usuario = self.bd.ejecutar_consulta(consulta = "SELECT * FROM usuario WHERE us_id_usuario = %s", valores = [id_usuario])[0][0]
            else:
                valores = (extraido, residencia_usuario, sexo_usuario, self.convertir_fecha(fecha_nac_usuario), id_usuario)
                self.bd.ejecutar_consulta(consulta = "UPDATE usuario SET us_extraido = %s, us_residencia = %s, us_sexo = %s, us_fecha_nacimiento = %s WHERE us_id_usuario = %s", valores = valores)
                return
        return id_usuario
            
    def guadarPost(self, url_post, texto, fecha_post, cantidad_comentarios, extraido, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira, id_usuario_post, medios, id_consulta):
        id_post = self.bd.ejecutar_consulta( consulta = 'SELECT * FROM post WHERE post_url = (%s) or post_texto = %s', valores = [url_post,texto] )
        try:
            if not id_post:
                consulta_post = 'INSERT INTO post (post_url, post_texto, post_fecha, post_comentarios, post_extraido, post_gusta, post_encanta, post_importa, post_risa, post_asombro, post_triste, post_ira, post_us_id, post_cons_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'                 
                valores_post = (url_post, texto, self.convertir_fecha(fecha_post), cantidad_comentarios, extraido, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira, id_usuario_post, id_consulta)
                post = False
                id_post = self.bd.ejecutar_consulta(consulta = consulta_post, valores = valores_post)
            else:                
                post = True
                consulta_post = 'UPDATE post SET post_fecha = %s, post_extraido = %s, post_comentarios = %s, post_gusta = %s, post_encanta = %s, post_importa = %s, post_risa = %s, post_asombro = %s, post_triste = %s, post_ira = %s WHERE post_id = %s'
                valores_post = (self.convertir_fecha(fecha_post), extraido, cantidad_comentarios, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira, id_post[0][0])
                self.bd.ejecutar_consulta( consulta = consulta_post, valores = valores_post )    
        except Exception as e:
            print(e)
    
        if not post:  
            try:
                consulta_medio = "INSERT INTO medios (med_link, med_post_id) VALUES (%s, %s)"
                for medio in medios:
                    valores_medios = (medio, id_post)
                    self.bd.ejecutar_consulta(consulta = consulta_medio, valores = valores_medios)
            except mysql.connector.errors.IntegrityError as e:
                print(e.errno)
                
    def guardar_comentario(self, comentario_post, fecha, procesado, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira , post_id, id_usuario_comentario):
        id_comentario = self.bd.ejecutar_consulta(consulta = "SELECT com_id FROM comentario WHERE com_texto = %s", valores = [comentario_post])      
        if not id_comentario:
            consula_comentario = "INSERT INTO comentario (com_texto, com_fecha, com_procesado, com_gusta, com_encanta, com_importa, com_risa, com_asombro, com_triste, com_ira, com_post_id, com_us_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            valores_comentario = (comentario_post, self.convertir_fecha(fecha), procesado, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira , post_id, id_usuario_comentario)
            id_comentario = self.bd.ejecutar_consulta(consulta = consula_comentario, valores = valores_comentario)
        else:
            consula_comentario = "UPDATE comentario SET com_fecha = %s, com_procesado = %s, com_gusta = %s, com_encanta = %s, com_importa = %s, com_risa = %s, com_asombro = %s, com_triste = %s, com_ira = %s WHERE com_id = %s"
            valores_comentario = (self.convertir_fecha(fecha), procesado, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira, id_comentario[0][0])     
            id_comentario = self.bd.ejecutar_consulta(consulta = consula_comentario, valores = valores_comentario)