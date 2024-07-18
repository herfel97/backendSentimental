# from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
# from selenium.webdriver.edge.service import Service
# from webdriver_manager.microsoft import EdgeChromiumDriverManager
# from selenium import webdriver
from controlador_basedatos import controlador_bd
from multiprocessing import Process, Queue, Manager
from conexion_db import ConexionBD
from PIL import Image
from io import BytesIO
import requests
import os
import re
import time

bd = ConexionBD()
ctrl_bd = controlador_bd()

def reacciones():
  global driver
  reacciones = driver.find_elements(By.XPATH, '/html/body/div/div/div[2]/div/table/tbody/tr/td/div/div/a')
  reaccion_like = reaccion_ira = reaccion_risa = reaccion_corazon = reaccion_asombro = reaccion_triste = reaccion_importa = 0
  
  def convertir_a_numero(valor):
    if "mil" in valor:
      valor = valor.replace("mil", "").strip()
      valor = valor.replace(",", ".")
      numero = float(valor) * 1000
      return int(numero)
    else:
      return int(valor)
      
  for i in range( len( reacciones ) ):
    if len(reacciones) > 1 and i < ( len(reacciones) - 1 ):
      posicion = i + 2
    elif len( reacciones ) == 1:
      posicion = i + 1
      
    xpath = f'/html/body/div/div/div[2]/div/table/tbody/tr/td/div/div/a[{posicion}]/img'
    reaccion = driver.find_element(By.XPATH, xpath).get_attribute('src')
    time.sleep(1)
    reaccion_img = requests.get(reaccion)
    imagen_bytes = BytesIO(reaccion_img.content)
    imagen_reaccion = Image.open(imagen_bytes)
    
    for imagen in os.listdir('img_reacciones'):
      ruta_archivo = os.path.join('img_reacciones', imagen)
      imagen_referencia = Image.open(ruta_archivo)
      
      if list( imagen_reaccion.getdata() ) == list( imagen_referencia.getdata() ):
        xpath_valor_reaccion = f'/html/body/div/div/div[2]/div/table/tbody/tr/td/div/div/a[{posicion}]/span'
        reaccion_valor = driver.find_element(By.XPATH, xpath_valor_reaccion).text
        if 'like' in ruta_archivo:
          reaccion_like = convertir_a_numero(reaccion_valor)
        elif 'corazon' in ruta_archivo:
          reaccion_corazon = convertir_a_numero(reaccion_valor)
        elif 'asombro' in ruta_archivo:
          reaccion_asombro = convertir_a_numero(reaccion_valor)
        elif 'ira' in ruta_archivo:
          reaccion_ira = convertir_a_numero(reaccion_valor)
        elif 'risa' in ruta_archivo:
          reaccion_risa = convertir_a_numero(reaccion_valor)
        elif 'importa' in ruta_archivo:
          reaccion_importa = convertir_a_numero(reaccion_valor)
        else:
          reaccion_triste = convertir_a_numero(reaccion_valor)
  time.sleep(3)
  driver.back()
  
  return reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira
       
def informacionUsuarios(link_usuario):
  global driver, extraccion_us, usuario_extraido, id_usuario, usuario_coment_extraido, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion
  
  residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion = "", "","",""
  
  # if not extraccion_us:
  if 'profile.php' in link_usuario:
    usuario_coment_extraido = re.search(r'(facebook?[^&]+)', link_usuario).group(0)
    id_usuario = re.search(r'((^id=)?(\d+)(^&)?)', link_usuario).group(1)    
  else:
    usuario_coment_extraido = re.search(r'(facebook.com/?[^/?]+)', link_usuario).group(0)
    id_usuario = re.search(r'/([^/]+)', usuario_coment_extraido).group().replace('/',"")
        
  usuario_coment_extraido = 'https://mbasic.'+usuario_coment_extraido
  usuario_coment_extraido = usuario_coment_extraido.replace(" ","")
  
  usuario_extraido = False if not bd.ejecutar_consulta(consulta = "SELECT us_id_usuario FROM usuario WHERE us_url = %s and us_extraido = %s", valores = [usuario_coment_extraido, 1]) else True
  if extraccion_us:
    if not usuario_extraido:
      
      residencia_usuario = fecha_nac_usuario = sexo_usuario = list_educacion = ''
      driver.get(usuario_coment_extraido+'/about')
      driver.refresh()
      time.sleep(3)
      
      try:
        residencia_usuario = driver.find_element(By.ID, 'living')
        residencia_usuario = residencia_usuario.find_elements(By.TAG_NAME, 'td')[3].text      
      except NoSuchElementException:
        residencia_usuario = ''
                                    
      try:
        valor = driver.find_element(By.ID, 'basic-info')
        valor = valor.find_elements(By.TAG_NAME, 'td')
        fecha_nac_usuario = valor[3].text if 'Fecha de' in valor[2].text else ''
        sexo_usuario = valor[3].text if 'Sexo' in valor[2].text else valor[5].text if 'Sexo' in valor[4].text else ''
      except NoSuchElementException:
        fecha_nac_usuario = ''
        sexo_usuario = ''
      except IndexError:
        fecha_nac_usuario = ''
        sexo_usuario = ''
        
      
      try:
        educacion_usuario = driver.find_elements(By.XPATH, '//div[@id = "education"]/div/div[2]/div/div/div/div[1]')
        list_educacion = []
        for educacion in educacion_usuario:
          list_educacion.append(educacion.text)       
      except NoSuchElementException:
        list_educacion = []
      
  return

def extraccion_medios(medios_link):
  global driver
  medios = []
  driver.execute_script("window.open('');")
  driver.switch_to.window(driver.window_handles[ len(driver.window_handles)-1 ])
  for medio in medios_link:
    driver.get( medio )
    if 'scontent' in driver.current_url:
      time.sleep(2)
      medios.append(driver.current_url)
    else:
      time.sleep(3)
      url_medio = driver.find_element(By.ID, 'root')
      url_medio = url_medio.find_element(By.TAG_NAME, 'img').get_attribute('src')
      medios.append(url_medio)
      
  driver.close()
  driver.switch_to.window(driver.window_handles[ len(driver.window_handles)-1 ])
  time.sleep(3)
  return medios
  
def extraccion_posts(driver_, busqueda, fecha_busqueda):
  global driver, extraccion_us, usuario_extraido, id_usuario, usuario_coment_extraido, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion
  driver = driver_
  extraccion_us = True
  driver.get(f'https://mbasic.facebook.com/search/posts/?q={busqueda}')
  time.sleep(2)
          
  id_consulta = bd.ejecutar_consulta('SELECT * FROM consulta where cons_busqueda = %s', [busqueda])
  if not id_consulta:
    id_consulta = bd.ejecutar_consulta('INSERT INTO consulta (cons_busqueda, cons_fecha) VALUES (%s, %s)', [busqueda, fecha_busqueda])
    bd.ejecutar_consulta('commit')
  else:
    id_consulta = id_consulta[0][0]
  while True:    
    try:
      bloqueo = driver.find_element(By.XPATH, '/html/body/div/div[1]/div[2]/div[2]/div[1]/span/div')
      if 'Parece que hiciste un uso indebido de esta función al ir muy rápido. Se te bloqueó su uso temporalmente.\n\nSi crees que esto no infringe nuestras Normas comunitarias, avísanos.' in bloqueo.text:            
        return 'Ocurrio un problema intente otra vez en unos instantes'          
    except Exception as e:
      error = ''      
            
    try:            
      posts = driver.find_elements(By.XPATH, '//div[@id = "BrowseResultsContainer"]/div[1]/div/div/div/div/div')      
      links_post = driver.find_elements(By.XPATH, '//div/a[contains(text(), "Historia completa")]')      
      i = 0
      for post, link_post in zip(posts, links_post):
        i += 1
        link_post = link_post.get_attribute('href')
        url_post = 'mbasic.'+re.search(r'mbasic.?(.*?)&eav', link_post).group(1)
        usuario = post.find_element(By.TAG_NAME, 'a').get_attribute('href')          
        path_text = f'//html/body/div/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/div/div/div/div[{i}]/div/div/div/div/div[1]/div[2]/div'
        texto = texto2 = ''
        mas = False
        try:
          texto = post.find_element(By.XPATH, path_text)
          link_mas = texto.find_elements(By.TAG_NAME, 'a')
          for j in link_mas:
            if 'Más' in j.text:
              mas = True
              break
        except NoSuchElementException as e:
          print('Error en extraccion de texto')
          
        try:
          path_rep = f'//html/body/div/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/div/div/div/div[{i}]/div/div/div/div/div[1]/div[3]/div'
          repost = driver.find_elements(By.XPATH, path_rep)
          if len(repost) > 2:
            path = f'//html/body/div/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/div/div/div/div[{i}]/div/div/div/div/div[1]/div[3]/div[1]'
          else:
            path_us_repos = f'//html/body/div/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/div/div/div/div[{i}]/div/div/div/div/div[1]/div[3]/div[2]/div/div/div[1]'
            usuario_rep = driver.find_element(By.XPATH, path_us_repos)              
            usuario_rep = usuario_rep.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            path_text_repos = f'//html/body/div/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/div/div/div/div[{i}]/div/div/div/div/div[1]/div[3]/div[2]/div/div/div[2]'
            texto2 = driver.find_element(By.XPATH, path_text_repos).text
            path = f'//html/body/div/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/div/div/div/div[{i}]/div/div/div/div/div[1]/div[3]/div[2]/div/div/div[3]'
            
          medios_links = post.find_element(By.XPATH, path)
          medios_links = medios_links.find_elements(By.TAG_NAME, 'a')
          lista_links_medios = []
          for medios_link in medios_links:
            if 'video_redirect' in medios_link.get_attribute('href') or 'photo' in medios_link.get_attribute('href'): 
              lista_links_medios.append(medios_link.get_attribute('href'))
        except NoSuchElementException:
          print("Error en extracion de medios")
          lista_links_medios = []
        
        # path_comentario = f'//html/body/div/div/div[2]/div[2]/div[1]/div[2]/div[1]/div/div/div/div/div[{i}]/div/div/div/div/div[2]/div[2]/a'
        comentario = post.find_element(By.XPATH,'//div[span[starts-with(@id, "like_")]]/a')
          
        if 'comentario' in comentario.text:            
          cantidad_comentarios = int( re.search(r'(?:\d+\D)+', comentario.text).group(0).replace(".","").replace(" ","") )
          cantidad_comentarios = cantidad_comentarios if cantidad_comentarios else 0
        else:
          cantidad_comentarios = 0
        fecha_post = post.find_element(By.TAG_NAME, 'abbr').text
        if not mas and texto:
          texto = texto.text
        
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link_post)
        time.sleep(3)  
              
        if mas:
          texto = driver.find_element(By.XPATH, '//html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[2]').text
        if driver.find_element(By.CSS_SELECTOR, '[id ^= "sentence_"] > a').text:
          reacciones_link = str(driver.find_element(By.CSS_SELECTOR, '[id ^= "sentence_"] > a').get_attribute('href'))
          driver.get(reacciones_link)
          time.sleep(4)
          reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira = reacciones()
        else:
          reaccion_like = reaccion_corazon = reaccion_importa = reaccion_risa = reaccion_asombro = reaccion_triste = reaccion_ira = 0
        time.sleep(5)
        medios = extraccion_medios(lista_links_medios)
        informacionUsuarios(usuario)
        if not usuario_extraido:
          time.sleep(4)
          id_usuario_post = ctrl_bd.guardarUsuario(id_usuario, usuario_coment_extraido, True, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion)
          bd.ejecutar_consulta('commit')
          driver.back()
        else:
          id_usuario_post = bd.ejecutar_consulta(consulta = "SELECT us_id FROM usuario WHERE us_url = %s", valores = [usuario_coment_extraido])[0][0]
          time.sleep(3)
        ctrl_bd.guadarPost(url_post, texto+texto2, fecha_post, cantidad_comentarios, False, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira, id_usuario_post, medios, id_consulta)
        bd.ejecutar_consulta('commit')
        time.sleep(5)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(4)          
                              
      link_ver_mas = str( driver.find_element(By.XPATH, '//div[@id = "see_more_pager"]/a').get_attribute('href') )
      driver.get(link_ver_mas)
      time.sleep(5)
    except NoSuchElementException:
      print('Fin de resultados')
      return 'Fin de publicaciones'
      break   

def info_comentarios(post_id, url_usuario, texto_comentario, texto_reaccion, url_reacciones, fecha, cola):
  global usuario_extraido, extraccion_us, id_usuario, usuario_coment_extraido, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion
  extraccion_us = False
  try:
    if texto_comentario:
      informacionUsuarios(url_usuario)
          
      if not usuario_extraido:      
        id_usuario_comentario = ctrl_bd.guardarUsuario(id_usuario, usuario_coment_extraido, False, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion)
        bd.ejecutar_consulta('commit')
      else:
        id_usuario_comentario = bd.ejecutar_consulta(consulta = "SELECT us_id FROM usuario WHERE us_url = %s", valores = [usuario_coment_extraido])[0][0]                     
        
      # time.sleep(4)  
      lista = [post_id, id_usuario_comentario, id_usuario, url_usuario, texto_comentario, texto_reaccion, url_reacciones, fecha]
      cola.put(lista)
    time.sleep(0.5)  
  except Exception as e:
    print('Error extracción comentarioñ ', e, ' id_us ', id_usuario )
    # lista = [post_id, id_usuario_comentario, id_usuario, url_usuario, texto_comentario, texto_reaccion, url_reacciones, fecha]

def comp(num):
  try:
      numero = float(num)  # Intenta convertir el texto a un número
      return True
  except ValueError:
      numero = None
      return False
    
def extraccion_comentarios_reacciones_mas_paralelo(post_id, comentarios, reaccion_por_comentarios, links_usuarios_comentario, fechas_comentarios):
  global driver
  # extraccion_us = False
  proceso_extraccion = []
  cola = Queue()
  for comentario, reaccion, usuario, fecha in zip(comentarios, reaccion_por_comentarios, links_usuarios_comentario, fechas_comentarios):
    proceso_e = Process(target=info_comentarios, args=(post_id, usuario.get_attribute('href'), comentario.text, reaccion.text, reaccion.get_attribute('href'),fecha.text, cola))
    proceso_extraccion.append(proceso_e)
    # info_comentarios(post_id, usuario.get_attribute('href'), comentario.text, reaccion.get_attribute('href'),fecha.text, cola)
  
  for i in proceso_extraccion:
    i.start()
  for i in proceso_extraccion:
    i.join()
  
  driver.execute_script("window.open('');")
  driver.switch_to.window(driver.window_handles[ len(driver.window_handles)-1 ])
  while not cola.empty():
    dato = cola.get_nowait()    
    if comp(dato[5]):
      driver.get(dato[6])
      # time.sleep(3)
      reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira = reacciones()
    else:
      reaccion_like = reaccion_corazon = reaccion_importa = reaccion_risa = reaccion_asombro = reaccion_triste = reaccion_ira = 0
      
    ctrl_bd.guardar_comentario(dato[4], dato[7], False, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira , post_id, dato[1])
    bd.ejecutar_consulta('commit')
  driver.close()
  driver.switch_to.window(driver.window_handles[ len(driver.window_handles)-1 ])
  time.sleep(2)
  
def extraccion_comentarios_reacciones_mas(post_id, comentarios, reaccion_por_comentarios, links_usuarios_comentario, fechas_comentarios):
  global driver, extraccion_us, usuario_extraido, id_usuario, usuario_coment_extraido, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion
  extraccion_us = False
  for comentario, reaccion, usuario, fecha in zip(comentarios, reaccion_por_comentarios, links_usuarios_comentario, fechas_comentarios):
    comentario_post = comentario.text
    if comentario_post:
      val_reaccion = reaccion.text
      link_usuario = str( usuario.get_attribute('href') )        
      link_reaccion_comentario = reaccion.get_attribute('href')
      driver.execute_script("window.open('');")
      driver.switch_to.window(driver.window_handles[ len(driver.window_handles)-1 ])      
      if comp(val_reaccion):
        driver.get(link_reaccion_comentario)
        time.sleep(2)
        reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira = reacciones()
      else:
        reaccion_like = reaccion_corazon = reaccion_importa = reaccion_risa = reaccion_asombro = reaccion_triste = reaccion_ira = 0
      informacionUsuarios(link_usuario)
      if not usuario_extraido:        
        id_usuario_comentario = ctrl_bd.guardarUsuario(id_usuario, usuario_coment_extraido, False, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion)
        bd.ejecutar_consulta('commit')
        driver.back()
      else:
        id_usuario_comentario = bd.ejecutar_consulta(consulta = "SELECT us_id FROM usuario WHERE us_url = %s", valores = [usuario_coment_extraido])[0][0]
              
      driver.close()
      driver.switch_to.window(driver.window_handles[ len(driver.window_handles)-1 ])         
      ctrl_bd.guardar_comentario(comentario_post, fecha.text, False, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira , post_id, id_usuario_comentario)
      bd.ejecutar_consulta('commit')
      time.sleep(1)  

def extraccion_rep_mas(link_re_comentario, id_post):
  global tipo
  driver.execute_script("window.open('');")
  driver.switch_to.window(driver.window_handles[ len(driver.window_handles)-1 ])
  driver.get(link_re_comentario)
  time.sleep(2)
  while True:
    try:
      anteriores = driver.find_element(By.XPATH, '//div[starts-with(@id, "comment_replies_more_1")]/a').get_attribute('href')
      driver.get(anteriores)
      time.sleep(2)
              
    except NoSuchElementException:
      print('Es lo ultimo de comentarios')
      break
    
  while True:
    try:
      comentarios = driver.find_elements(By.XPATH, '//div[@id = "root"]/div[1]/div[3]/div/div/div[1]')
      usuarios_comentarios = driver.find_elements(By.XPATH, '//div[@id = "root"]/div[1]/div[3]/div/div/h3/a')
      reacciones_comentarios = driver.find_elements(By.XPATH, '//span[starts-with(@id, "like_")]/span/a[1]')
      fechas_comentarios = driver.find_element(By.XPATH, '//div[@id = "root"]/div[1]/div[3]')
      fechas_comentarios = fechas_comentarios.find_elements(By.TAG_NAME, 'abbr')              
      reacciones_comentarios.pop(0)
      if tipo == 'rapido':
        extraccion_comentarios_reacciones_mas_paralelo(id_post, comentarios, reacciones_comentarios, usuarios_comentarios, fechas_comentarios)
      else:      
        extraccion_comentarios_reacciones_mas(id_post, comentarios, reacciones_comentarios, usuarios_comentarios, fechas_comentarios)
      mas = driver.find_element(By.XPATH, '//div[starts-with(@id, "comment_replies_more_2")]/a')
      driver.get( mas.get_attribute('href') )
      time.sleep(2)
      driver.refresh() 
    except NoSuchElementException:
      print('No mas comentarios')
      time.sleep(1)
      break
  
  driver.close()
  driver.switch_to.window(driver.window_handles[ len(driver.window_handles)-1 ])

def extraccion_respuestas(lks_comentarios, post_id):
  global extraccion_us, usuario_extraido, id_usuario, usuario_coment_extraido, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion
  extraccion_us = False
  for i in lks_comentarios:
    link_mas = i.find_elements(By.TAG_NAME, 'a')
    if len(link_mas) > 2:
      link_re = link_mas[2].get_attribute('href')
      extraccion_rep_mas(link_re, post_id)
    elif link_mas[0].text == '':
      usuario = link_mas[0].get_attribute('href')
      rep_comentario = i.find_element(By.TAG_NAME, 'span').text
      reaccion_like = reaccion_corazon = reaccion_importa = reaccion_risa = reaccion_asombro = reaccion_triste = reaccion_ira = 0
      
      informacionUsuarios(usuario)
      if not usuario_extraido:
        time.sleep(2)
        id_usuario_comentario = ctrl_bd.guardarUsuario(id_usuario, usuario_coment_extraido, False, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion)
        driver.back()
      else:
        id_usuario_comentario = bd.ejecutar_consulta(consulta = "SELECT us_id FROM usuario WHERE us_url = %s", valores = [usuario_coment_extraido])[0][0]
        
      ctrl_bd.guardar_comentario(rep_comentario, '', False, reaccion_like, reaccion_corazon, reaccion_importa, reaccion_risa, reaccion_asombro, reaccion_triste, reaccion_ira , post_id, id_usuario_comentario)                                
    else:
      link_re = link_mas[0].get_attribute('href')
      if 'comment/replies' in link_re:
        extraccion_rep_mas(link_re, post_id)    

def extraccion_comentarios(driver_, id_post, url_post, _tipo):
  global driver, tipo
  tipo = _tipo
  driver = driver_
  url = 'https://'+url_post
  driver.get(url)
  time.sleep(3)
  while True:
    try:
      anteriores = driver.find_element(By.XPATH, '//div[starts-with(@id, "see_prev_")]/a')
      driver.get(anteriores.get_attribute('href'))
      time.sleep(2)
    except Exception as e:
      error = e
      break
      
  while True:
    try:
      try:
        while True:
          bloqueo = driver.find_element(By.XPATH, '/html/body/div/div[1]/div[2]/div[2]/div[1]/span/div')
          if 'Parece que hiciste un uso indebido de esta función al ir muy rápido. Se te bloqueó su uso temporalmente.\n\nSi crees que esto no infringe nuestras Normas comunitarias, avísanos.' in bloqueo.text:            
            return 'Ocurrio un problema intente otra vez en unos instantes'          
      except Exception as e:
        error = ''      
      links_usuarios_comentario = driver.find_elements(By.XPATH, '//div[starts-with(@id, "ufi_")]/div/div[5]/div/div/h3/a')
      comentarios = driver.find_elements(By.XPATH, '//div[starts-with(@id, "ufi_")]/div/div[5]/div/div/div[1]')
      reaccion_por_comentarios = driver.find_elements(By.XPATH, '//span[starts-with(@id, "like_")]/span/a[1]')
      if not links_usuarios_comentario and not comentarios:
        links_usuarios_comentario = driver.find_elements(By.XPATH, '//div[starts-with(@id, "ufi_")]/div/div[4]/div/div/h3/a')
        comentarios = driver.find_elements(By.XPATH, '//div[starts-with(@id, "ufi_")]/div/div[4]/div/div/div[1]')        
        
      fechas_comentarios = driver.find_element(By.XPATH, '//div[starts-with(@id, "ufi_")]')
      fechas_comentarios = driver.find_elements(By.TAG_NAME, 'abbr')
      fechas_comentarios.pop(0)
      if tipo == 'rapido':
        extraccion_comentarios_reacciones_mas_paralelo(id_post, comentarios, reaccion_por_comentarios, links_usuarios_comentario, fechas_comentarios)
      else:
        extraccion_comentarios_reacciones_mas(id_post, comentarios, reaccion_por_comentarios, links_usuarios_comentario, fechas_comentarios)
        
      # extraccion_comentarios_reacciones_mas(id_post, comentarios, reaccion_por_comentarios, links_usuarios_comentario, fechas_comentarios)
      try:
        rep_comentario_links = driver.find_elements(By.XPATH, '//div[starts-with(@id, "comment_replies_more_")]')
        extraccion_respuestas(rep_comentario_links, id_post)
      except NoSuchElementException:
        print("no rep")
      
      driver.refresh()
      try:
        mas_comentarios = driver.find_element(By.XPATH, '//div[starts-with(@id, "see_next_")]/a').get_attribute('href')
        driver.get(mas_comentarios)
        time.sleep(2)
      except Exception as e:       
        return 'Finalizo la extracción'
    except Exception as e:      
      print("No hay mas comentarios FIN EXTRACCIÓN")
      return 'Finalizo la extracción error'
      
    
# def extraccion_usuarios(driver_, id_us, url_perfil):
#   global driver, extraccion_us, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion
#   driver = driver_
#   extraccion_us = True
#   # url = 'https://'+url_perfil
#   informacionUsuarios(url_perfil)
#   ctrl_bd.guardarUsuario(id_us, url_perfil, True, residencia_usuario, sexo_usuario, fecha_nac_usuario, list_educacion)
#   time.sleep(6)