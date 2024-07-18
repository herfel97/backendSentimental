from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from flask import Flask, request, Blueprint, jsonify
from conexion_db import ConexionBD
from controlador_chatGPT import controlador_chatgpt
from controlador_sentimientos import extraccion_posts, extraccion_comentarios
from datetime import datetime
from flask_cors import CORS
from threading import Lock
from multiprocessing import Process
import re
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
prefijo = '/FPSA/api'
bd = ConexionBD()
ctrl_gpt = controlador_chatgpt()

def login():
    global driver, webdrivers, num
    try:
        # driver = webdriver.ChromiumEdge( service = Service(EdgeChromiumDriverManager( version='113.0.1774.57' ).install()) )                
        url_wqeb = 'http://selenium-hub:4444/wd/hub'
        # url_wqeb = 'http://172.16.26.27:4444/wd/hub'
        options = EdgeOptions()
        options.platform_name = 'Linux'
        driver = webdriver.Remote(
            command_executor=url_wqeb,
            options=options
        )
        webdrivers.append(driver)
        driver.get("https://mbasic.facebook.com/")
        email = driver.find_element(By.ID, 'm_login_email')
        password = driver.find_element(By.NAME, 'pass')
        if num == 1:
            email.send_keys('bryamedup@gmail.com')
            password.send_keys('Bepz01075*')
        elif num == 2:
            email.send_keys('mifeyi4350@bodeem.com')
            password.send_keys('3rt1-ytrewq')
        elif num == 3:
            email.send_keys('yidepok889@bodeem.com')
            password.send_keys('3rt1-ytrewq')
        elif num == 4:
            email.send_keys('hegejol771@akoption.com')
            password.send_keys('3rt1-ytrewq')
        elif num == 5:
            # email.send_keys('brayamcampeon-dosuno2709@hotmail.com')
            email.send_keys('cast252625@gmail.com')
            password.send_keys('Ju@n2629')
        else:
            return "Ocurrio un problema intente otra vez en unos instantes"        
        
        # password.send_keys('3rt1-ytrewq')
        boton_inicio = driver.find_element(By.NAME, 'login')
        boton_inicio.click()
        
        if 'https://mbasic.facebook.com/login/save-device/?login_source' in driver.current_url:        
            driver.find_element(By.XPATH, '//input[@type = "submit"]').click()    
            return 'login'            
        else:
            print("Error")
    except Exception as e:
        print(e)
        return "Error de inicio"
        
@app.route(f'{prefijo}/Cancelar', methods=['GET'])
def cancelarWeb():
    global webdrivers    
    with lock:
        try:
            if webdrivers:
                for driver in webdrivers:
                    try:
                        driver.quit()
                    except Exception as e:
                        print(f"Error al cerrar webdriver: {e}")
                # Limpia la lista de webdrivers después de cerrarlos
                webdrivers.clear()
        except Exception as e:
            print(e)    
        return jsonify("Consulta Cancelada")
        
@app.route(f'{prefijo}/busqueda', methods = ['POST'])
def post():
    global driver, webdrivers, lock, cancelar, num 
    busqueda = request.get_json().get('busqueda').upper()
    fecha_busqueda = datetime.now().date()
    num = 1
    texto = ''
    try:
        login()
        start = time.time()
        
        while True:
            texto = extraccion_posts(driver, busqueda, fecha_busqueda)
            if texto != 'Ocurrio un problema intente otra vez en unos instantes':
                print('saliendo..')
                break
            else:
                driver.quit()
                num += 1
                login()
        end = time.time()
        driver.quit()
        bd.ejecutar_consulta('commit')
        tiempo = end - start
        if not 'Ocurrio un problema intente otra vez en unos instantes' in texto:
            return jsonify({'mensaje':"Extraccion completada", 'tiempo':tiempo})
        else:
            return jsonify({'mensaje':'Ocurrio un problema intente otra vez en unos instantes'})            
    except Exception as e:        
        if webdrivers:
            driver.quit()
        bd.ejecutar_consulta('commit')
        return jsonify({'mensaje':"Extracción incompleta, Fin extracción"})
        
@app.route(f'{prefijo}/all_posts', methods = ['GET'])
def all_posts():
    posts = bd.ejecutar_consulta("SELECT post.*, COALESCE(total_filas.total_filas_relacionadas, 0) AS total_filas_relacionadas \
                                FROM sentimientos_db.post \
                                LEFT JOIN ( \
                                    SELECT com_post_id, COUNT(*) AS total_filas_relacionadas \
                                    FROM sentimientos_db.comentario \
                                    GROUP BY com_post_id \
                                ) AS total_filas ON post.post_id = total_filas.com_post_id \
                                ORDER BY post.post_fecha")
    json_all = jsonify(posts)
    return json_all

@app.route(f'{prefijo}/post_id', methods = ['GET'])
def post_id():
    id_post =  request.args.get('id')
    post = bd.ejecutar_consulta("SELECT post.*, COALESCE(total_filas.total_filas_relacionadas, 0) AS total_filas_relacionadas \
                                FROM sentimientos_db.post \
                                LEFT JOIN ( \
                                    SELECT com_post_id, COUNT(*) AS total_filas_relacionadas \
                                    FROM sentimientos_db.comentario \
                                    GROUP BY com_post_id \
                                ) AS total_filas ON post.post_id = total_filas.com_post_id \
                                WHERE post_cons_id = %s \
                                ORDER BY post.post_fecha", [id_post])
    return jsonify(post) if post else jsonify(" Consulta sin extracción. error")

# MEtodo para mostrar las consultas
@app.route(f'{prefijo}/posts_consulta', methods = ['GET'])
def post_consulta():
    
    posts = bd.ejecutar_consulta("SELECT * FROM sentimientos_db.consulta")
    post_c = []
    for post in posts:
        p = []
        p.append(post[0])
        p.append(post[1].title())
        p.append(post[2])
        post_c.append(p)
        
    return jsonify(post_c)
        

@app.route(f'{prefijo}/comentarios_post', methods = ['POST'])
def extraer_comentarios_posts():
    global driver, num
    num = 1
    posts_seleccionados = request.get_json().get('lista')
    tipo = request.get_json().get('tipo')
    texto = ''
    try:    
        login()
        start = time.time()
        end = 0
        for items in posts_seleccionados:
            id_post = int( items['id'] )
            url_post = items['url']            
            bd.ejecutar_consulta("UPDATE post SET post_extraido = %s WHERE post_id = %s", [True, id_post])
            bd.ejecutar_consulta('commit')
            while True:
                texto = extraccion_comentarios(driver, id_post, url_post, tipo)
                if texto != 'Ocurrio un problema intente otra vez en unos instantes':
                    print('saliendo..')
                    break
                else:
                    driver.quit()
                    num += 1
                    login()
        end = time.time()
        driver.quit()
    except Exception as e:
        print("Ocurrio un problema > ", e)
        return jsonify({'mensaje':'Ocurrio un problema intente otra vez en unos instantes'})
    finally:
        print("se acabo")
        # if driver:
        #     driver.quit()
        for item in posts_seleccionados:
            com = bd.ejecutar_consulta("SELECT count(*) FROM comentario WHERE com_post_id = %s", [item['id']])
            if com[0][0] == 0:
                bd.ejecutar_consulta("UPDATE post SET post_extraido = %s WHERE post_id = %s", [False, id_post])
        bd.ejecutar_consulta('commit')
        tiempo = end-start
        if not 'Ocurrio un problema intente otra vez en unos instantes' in texto:
            return jsonify({'mensaje':'Extracción completada','tiempo':tiempo})
        else:
            return jsonify({'mensaje':'Ocurrio un problema intente otra vez en unos instantes'})            

@app.route(f'{prefijo}/all_comentarios', methods = ['GET'])
def all_comentarios():    
    all_comentarios = bd.ejecutar_consulta("SELECT * FROM sentimientos_db.comentario")
    json_all_comentarios = jsonify(all_comentarios)
    return json_all_comentarios

@app.route(f'{prefijo}/comentarios_por_post', methods = ['GET'])
def comentarios_por_post():
    id_posts =  request.args.get('id_post')
    bd.ejecutar_consulta('commit')
    comentarios = bd.ejecutar_consulta("SELECT * FROM comentario WHERE com_post_id = %s", [id_posts])
    json_comentarios_p = jsonify(comentarios)
    return json_comentarios_p if comentarios else jsonify("No han sido extraidos los comentarios de esta publicación")

def analizar_comentarios(id, comentario):
    texto = 'Analiza el siguiente texto y clasifica el sentimiento en una palabra (positivo, negativo o neutro). Luego, proporciona una breve justificación (máximo 3 líneas) \
                explicando por qué consideras ese sentimiento. \
                    imprime obedeciendo la siguiente estructura: \
                        Sentimiento: Sentimientos analizando del texto \
                        Justificacion: Justificacion del texto \
                \nTexto a analizar:\n'
    texto += comentario
    respuesta = ctrl_gpt.enviar_promt(texto)
    sentimiento_split = re.split('\nJustificación: |\nJustificaciòn: |Justificacion: ', respuesta)
    try:
        sentimiento = re.split('.\n\nSentimiento: |\n\nSentimiento: |Sentimiento: ', sentimiento_split[0])[1]
        if 'Positivo' in sentimiento:
            sentimiento = 'Positivo'
        elif 'Negativo' in sentimiento:
            sentimiento = 'Negativo'
        elif 'Neutro':
            sentimiento = 'Neutro'
        justificacion = sentimiento_split[1]
    except Exception as e:
        print(e)
    try:
        bd.ejecutar_consulta("UPDATE comentario SET com_procesado = 1, com_sentimiento = %s, com_respuesta = %s WHERE com_id = %s", (sentimiento, justificacion, id))
        bd.ejecutar_consulta('commit')
    except Exception as e:
        print(e)
        bd.ejecutar_consulta("UPDATE comentario SET com_procesado = 1, com_sentimiento = %s, com_respuesta = %s WHERE com_id = %s", (sentimiento, justificacion, id))

@app.route(f'{prefijo}/analizar_sentimientos', methods = ['POST'])
def analizar():
    post_por_analizar = request.get_json().get('id_post')
    tipo = request.get_json().get('tipo')
    comentarios_post = bd.ejecutar_consulta("SELECT com_id, com_texto FROM comentario WHERE com_post_id = %s", [ post_por_analizar ])
    start = time.time()    
    if tipo == 'rapido':
        procesos = []
        for comentarios in comentarios_post:
            proceso = Process(target = analizar_comentarios, args = (comentarios[0], comentarios[1]) )
            procesos.append(proceso)            
                            
        grupos_procesos = [procesos[i:i+10] for i in range(0, len(procesos), 10)]

        for grupo in grupos_procesos:
            for proceso in grupo:
                proceso.start()
            for proceso in grupo:
                proceso.join()
    else:
        for comentarios in comentarios_post:
            analizar_comentarios(comentarios[0], comentarios[1])
    end = time.time()
    tiempo = end - start
    bd.ejecutar_consulta('commit')
    return jsonify({'mensaje':'Análisis completado','tiempo':tiempo})
 
@app.route(f'{prefijo}/analizar_sentimientos_posts', methods = ['POST'])
def analizar_com_posts():
    tipo = request.get_json().get('tipo')
    post_por_analizar = request.get_json().get('lista')
    start = time.time()
    if tipo == 'rapido':
        for post in post_por_analizar:
            comentarios = bd.ejecutar_consulta("SELECT com_id, com_texto FROM comentario WHERE com_post_id = %s", [ post['id'] ])
            procesos = []
            for i in range( len(comentarios) ):
                comentario = comentarios[i]                                
                proceso = Process(target = analizar_comentarios, args = (comentario[0], comentario[1]) )
                procesos.append(proceso)            
                            
            grupos_procesos = [procesos[i:i+5] for i in range(0, len(procesos), 5)]

            for grupo in grupos_procesos:
                for proceso in grupo:
                    proceso.start()
                for proceso in grupo:
                    proceso.join()
    else:
        for post in post_por_analizar:
            comentarios = bd.ejecutar_consulta("SELECT com_id, com_texto FROM comentario WHERE com_post_id = %s", [ post['id'] ])
            for i in range( len(comentarios) ):
                comentario = comentarios[i]
                analizar_comentarios(comentario[0], comentario[1])
    end = time.time()                
    tiempo = end - start
    bd.ejecutar_consulta('commit')                                        
    return jsonify({'mensaje':'Análisis completado','tiempo':tiempo})

@app.route(f'{prefijo}/sentimientos', methods = ['GET'])
def sentimientos_global():
    valor = bd.ejecutar_consulta('SELECT com_sentimiento, COUNT(*) AS count_valor \
                                 FROM sentimientos_db.comentario GROUP BY com_sentimiento')
    return jsonify(valor)

@app.route(f'{prefijo}/reacciones', methods = ['GET'])
def reacciones_global():
    valor = bd.ejecutar_consulta('SELECT \
                SUM(post_gusta) AS sum_gusta, \
                SUM(post_encanta) AS sum_encanta, \
                SUM(post_importa) AS sum_importa, \
                SUM(post_risa) AS sum_risa, \
                SUM(post_asombro) AS sum_asombro, \
                SUM(post_triste) AS sum_triste, \
                SUM(post_ira) AS sum_ira \
                FROM sentimientos_db.post;')
    
    return jsonify(valor)

@app.route(f'{prefijo}/sentimientos_consulta', methods = ['GET'])
def sentimientos_consulta():    
    consulta_query = f'SELECT com_sentimiento, COUNT(*) AS count_valor, cons_busqueda, post_fecha \
                                FROM sentimientos_db.comentario \
                                JOIN sentimientos_db.post ON comentario.com_post_id = post.post_id \
                                JOIN sentimientos_db.consulta ON post.post_cons_id = consulta.cons_id \
                                GROUP BY com_sentimiento, cons_busqueda, post_fecha \
                                ORDER BY post_fecha'
    sent_cons = bd.ejecutar_consulta(consulta_query)
    return jsonify(sent_cons)
    
@app.route(f'{prefijo}/reacciones_consulta', methods = ['GET'])
def reacciones_consulta():
    reaccion = request.args.get('reaccion')
    reaccion_query = f'SELECT {reaccion}, cons_busqueda, post_fecha \
                        FROM sentimientos_db.post \
                        JOIN sentimientos_db.consulta ON post.post_cons_id = consulta.cons_id \
                        GROUP BY {reaccion}, cons_busqueda, post_fecha  \
                        ORDER BY post_fecha'
    reacciones_consulta = bd.ejecutar_consulta(reaccion_query)
    return jsonify(reacciones_consulta)

if __name__ == '__main__':
    global webdrivers, cancelar, lock
    webdrivers = []
    cancelar = False   
    lock = Lock()
    app.run(host="0.0.0.0", port=int("5001"), debug=False)    