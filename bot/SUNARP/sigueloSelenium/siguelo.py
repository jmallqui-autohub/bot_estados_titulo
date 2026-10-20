import os
import time
import pyautogui
import traceback
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from utils.logger import Logger
from utils.funciones import human_pause
from resources.datosfijos import *
from utils.funciones import *
from middleware.funciones_correo import *
from middleware.apis import *
from bot.LECTURAPDF.estados_funciones import *
from utils.html import *

def cloudflare():
    #time.sleep(20)
    #print('hola')
    #mx,my=pyautogui.position()
    #print(mx,my)
    #input('adios')
    #741
    try:
        for i in range(2):
            pyautogui.click(396,710)
            #pyautogui.click(356,660)
            if i<1:time.sleep(25)
    except:
        print('Fallo al darle click al cloudflare')

def login_siguelo(historial:Logger,registro,driver:WebDriver):
    try:
        time.sleep(2)
        driver.get('https://sigueloplus.sunarp.gob.pe/siguelo/')
        driver.implicitly_wait(5)
        #driver.maximize_window()
        try:
            driver.find_element(By.CSS_SELECTOR,'#mat-dialog-0 > mat-dialog-actions>button:nth-child(2)').click()
            print('Se hizo click en el boton de ignorar')
        except:pass

        WebDriverWait(driver,5).until(EC.presence_of_element_located((By.CSS_SELECTOR,"#cboOficina")))
        Select(driver.find_element(By.CSS_SELECTOR,'#cboOficina')).select_by_visible_text(registro['oficina'])
        WebDriverWait(driver,5).until(EC.presence_of_element_located((By.CSS_SELECTOR,"#cboAnio")))
        Select(driver.find_element(By.CSS_SELECTOR,'#cboAnio')).select_by_value(registro['anio'])

        WebDriverWait(driver,5).until(EC.presence_of_element_located((By.CSS_SELECTOR,"#interno > div > div > form > div:nth-child(7) > div > div > input")))
        selector_titulo=driver.find_element(By.CSS_SELECTOR,'#interno > div > div > form > div:nth-child(7) > div > div > input')
        for letra in registro['titulo']:
            selector_titulo.send_keys(letra)
            human_pause()
        WebDriverWait(driver,5).until(EC.text_to_be_present_in_element_value((By.CSS_SELECTOR,"#interno > div > div > form > div:nth-child(7) > div > div > input"),registro['titulo']))
        cloudflare()
        time.sleep(2)
        WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#interno > div > div > form > div:nth-child(10) > div > div > button")))
        driver.find_element(By.CSS_SELECTOR,'#interno > div > div > form > div:nth-child(10) > div > div > button').click()
        time.sleep(2)
        #VERIFICAMOS SI SALE EL POP UP CON EL MENSAJE DE ERROR O XQ NO ESPERO LA CARGA DEL CLOUDFARE
        try:
            elemento=driver.find_elements(By.CSS_SELECTOR,'#swal2-content > p')
            if len(elemento)>0:
                mensaje_popup=driver.find_element(By.CSS_SELECTOR,'#swal2-content > p').get_attribute('innerText')
                if mensaje_popup and mensaje_popup in LISTA_MENSAJES_SIGUELO:
                    historial.obs(f'mensaje encontrado: {mensaje_popup}')
                    driver.find_element(By.CSS_SELECTOR,'body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled').click()
                    time.sleep(2)
                    driver.find_element(By.CSS_SELECTOR,'#interno > div > div > form > div:nth-child(10) > div > div > button').click()
            elemento=driver.find_elements(By.CSS_SELECTOR,'#swal2-content > table > tfoot > tr > td')
            if len(elemento)>0:
                mensaje_popup=driver.find_element(By.CSS_SELECTOR,'#swal2-content > table > tfoot > tr > td').get_attribute('innerText')
                if mensaje_popup and mensaje_popup.strip() =='429':
                    historial.obs(f"Mensaje de error encontrado: {mensaje_popup}")
                    historial.error(f'El bot se encuentra baneado')
                    enviar_webhoook(f'BOT-{os.getenv("BOT_ASIGNADO")}','URGENTE','Estado del bot','El bot se encuentra baneado por el sitio de consulta, se detiene el proceso de consultas de bot, se espera respuesta del usuario')
                    historial.info(f'Se detiene el proceso de consultas de bot, se espera respuesta del usuario')
                    notificar_bot(historial)
                    respuesta_usuario=pausar_bot(historial)
                    if respuesta_usuario:
                        driver.refresh()
                        login_siguelo(historial,registro,driver)
                    else:
                        historial.info('No hubo respuesta del usuario se procede al cierre del bot ')
                        enviar_webhoook(f'BOT-{os.getenv("BOT_ASIGNADO")}','URGENTE','Estado del bot','No hubo respuesta del usuario para continuar con el proceso del bot, se procede al cierre del bot')
                        sys.exit()
                elif mensaje_popup and mensaje_popup.strip()=='0002':
                    historial.obs(f"Mensaje de error encontrado: {mensaje_popup}")
                    historial.error(f'Error en los datos de la consulta')
                    raise Exception(f'Error en los datos de la consulta {registro['inmatriculacion']}')    
        except Exception as e:
            raise Exception(e)
        time.sleep(2)
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CSS_SELECTOR,"body > div:nth-child(6) > div:nth-child(2) > div > input")))
        time.sleep(2)
    except Exception as e:
        historial.error(f'Fallo en el login de siguelo: {e}')
        raise Exception(f'Fallo en el login de siguelo. {e}')
def descargar_documentos_inscripcion(historial:Logger,driver:WebDriver,registro,ruta_descargas,contador,contador_inscripcion):
    #CREACION DE LA CARPETA
    ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{registro["titulo"]}-{registro["anio"]}')
    os.makedirs(ruta_carpeta, exist_ok=True)
    valor_selector= 0 if contador >1 else 1
    #DESCARGA DE LA ANOTACION
    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(5) > td > a > span"))).click()
    mover_archivos(ruta_descargas,ruta_carpeta,'ANOTACION')
    historial.info('Anotacion descargada')

    #DESCARGA DE LA INSCRIPCION
    try:
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(4) > td > a > span"))).click()
        time.sleep(5)
        WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,f'#mat-dialog-{valor_selector} > app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(3)'))).click()
        #driver.find_element(By.CSS_SELECTOR,f'#mat-dialog-{valor_selector} > app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(3)').click()
        if not mover_archivos(ruta_descargas,ruta_carpeta,registro['titulo']):
            historial.error('No se encontro el archivo de la inscripcion descargada')
            driver.find_element(By.CSS_SELECTOR,f'#mat-dialog-{valor_selector} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
        historial.info('Se descargo la inscripcion')
        placa=driver.find_element(By.CSS_SELECTOR,f'#mat-dialog-{valor_selector} > app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(4)').get_attribute('innerText')
        placa=placa.upper().strip()
        historial.obs(f'la placa {placa}')
        registro['placa']=placa
    except Exception as e:
        contador_inscripcion+=1
        if contador_inscripcion==2:
            historial.obs(f'Fallo la en el proceso de la descarga de la inscripcion o obtencion de la placa se intentara nuevamente')
            driver.refresh()
            descargar_documentos_inscripcion(historial,driver,registro,ruta_descargas,contador,contador_inscripcion)
        if contador_inscripcion==3:
            imagen_b64=driver.get_screenshot_as_base64()
            html_mensaje=generar_html_errores_siguelo(imagen_b64,registro)
            enviar_correo(CORREOS_ERROR,'ERROR INSCRIPCION',html_mensaje,1,'','','',historial,html=True)
        registro['observacion']='Fallo al descargar la inscripcion'
        historial.error(f'Fallo la descarga de la inscripcion: {e}')
        raise Exception('Fallo la descarga de la inscripcion')

    #DESCARGA DE LA TIVE
    try:
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,f"#mat-dialog-{valor_selector} > app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(5) > button"))).click()
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#swal2-content > p > b')))
        input_placa=driver.find_element(By.CSS_SELECTOR,'body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-content > input.swal2-input')
        for letra in registro['placa']:
            input_placa.send_keys(letra)
            human_pause()
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled"))).click()
        time.sleep(1)
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#swal2-content > p > b')))
        input_codVeri=driver.find_element(By.CSS_SELECTOR,'body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-content > input.swal2-input')
        for letra in registro['codigover']:
            input_codVeri.send_keys(letra)
            human_pause()
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled"))).click()
        if not mover_archivos(ruta_descargas,ruta_carpeta,f'{registro["placa"]}_TIVE'):
            historial.error('No se encontro el archivo de la tive descargada')
            driver.find_element(By.CSS_SELECTOR,f'#mat-dialog-{valor_selector} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
            raise Exception(f'Fallo la descarga de la tive')
        historial.info('Se descargo la tive')
    except Exception as e:
        registro['observacion']='Fallo al descargar la tive'
        historial.error(f'Fallo la descarga de la tive:{e}')
        raise Exception('Fallo la descarga de la tive')

    #DESCARGA DE LA ORDEN DE GIRO
    try:
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,f"#mat-dialog-{valor_selector} > app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(6) > button"))).click()
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#swal2-content > p > b')))
        input_placa=driver.find_element(By.CSS_SELECTOR,'body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-content > input.swal2-input')
        for letra in registro['placa']:
            input_placa.send_keys(letra)
            human_pause()
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled"))).click()
        time.sleep(1)
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#swal2-content > p > b')))
        input_codVeri=driver.find_element(By.CSS_SELECTOR,'body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-content > input.swal2-input')
        if not  registro['codigover'] or registro['codigover'].upper()=='FALSE' or registro['codigover'].upper()=='FALSO' or len(registro['codigover'])!=8:
            contador_intentos=obtener_contador_intentos(registro['inmatriculacion'])
            contador_intentos+=1
            actualizar_bitacora(registro,intentos=contador_intentos)
            raise Exception('Codigo de verificacion no valido para la consulta. Verificar')
        for letra in registro['codigover']:
            input_codVeri.send_keys(letra)
            human_pause()
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled"))).click()
        time.sleep(1)
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled"))).click()
        respuesta=mover_archivos(ruta_descargas,ruta_carpeta,f'{registro["placa"]}_ORDEN_GIRO')
        if not respuesta:
            mensaeje_orden_giro=driver.find_element(By.CSS_SELECTOR,'#swal2-content > table > tbody > tr > td > p')
            mensaje=mensaeje_orden_giro.get_attribute('innerText')
            historial.debug(mensaje)
            ruta_orden_giro=os.path.join(ruta_carpeta,f'{registro["placa"]}_ORDEN_GIRO.pdf')
            if os.path.exists(ruta_orden_giro):
                historial.obs("La orden de giro fue descargada anteriormente")
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                driver.find_element(By.CSS_SELECTOR,f'#mat-dialog-{valor_selector} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
            else:
                registro['estadosiguelo']='INSCRITO'
                registro['estado']='INCOMPLETO'
                registro['observacion']=mensaje
                raise Exception(mensaje)
        else:
            historial.info('Se descargo la orden de giro')
            driver.find_element(By.CSS_SELECTOR,f'#mat-dialog-{valor_selector} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
    except Exception as e:
        raise Exception(f'Fallo la descarga de la orden de giro:{e}')
    time.sleep(2)
def descargar_documentos_observados(driver:WebDriver,registro,ruta_descargas):
    try:
        ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{registro["titulo"]}-{registro["anio"]}')
        os.makedirs(ruta_carpeta, exist_ok=True)
        #DESCARGA ESQUELA DE OBSERVACION
        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(1) > td > a > span'))).click()
        cont=0
        lista_botones_observados = [] 
        
        while True:
            cont+=1
            WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#gridDiv > table > tbody')))
            tabla=driver.find_element(By.CSS_SELECTOR,'#gridDiv > table > tbody')
            filas=tabla.find_elements(By.TAG_NAME,'tr')
            nro_filas=len(filas)
            print(f'Numero de filas encontradas: {nro_filas} en la pagina {cont}')
            
            for i in range(nro_filas):
                valor_area = driver.find_element(By.CSS_SELECTOR,f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(2) > p').get_attribute('innerText')
                valor_area = valor_area.upper().strip()
                
                valor_estado=driver.find_element(By.CSS_SELECTOR,f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(3) > p:nth-child(2) > span').get_attribute('innerText')
                valor_estado=valor_estado.upper().strip()
                
                print(f'Fila {i+1}: Area={valor_area}, Estado={valor_estado}')
                
                if valor_estado=='OBSERVADO' and 'SECCION REGISTRAL' in valor_area:
                    valor=driver.find_elements(By.CSS_SELECTOR,f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(5)')
                    if valor:
                        lista_botones_observados.append({
                            'pagina': cont,
                            'fila': i+1,
                            'selector': f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(5) > div > a',
                            'area': valor_area
                        })
                        print(f'  ✓ Observación SECCION REGISTRAL encontrada en página {cont}, fila {i+1}')
                elif valor_estado=='OBSERVADO':
                    print(f'  ✗ Observación ignorada (no es SECCION REGISTRAL): {valor_area}')
            
            lista_boton_siguiente=driver.find_elements(By.CSS_SELECTOR,'body > div:nth-child(3) > div.col-sm-9 > div > div.nav-div > div > pagination-controls > pagination-template > ul > li.pagination-next.ng-star-inserted')
            
            if len(lista_boton_siguiente) > 0:
                boton_siguiente = lista_boton_siguiente[0]
                clases = boton_siguiente.get_attribute('class')
                esta_deshabilitado = 'disabled' in clases if clases else False
                
                print(f'Botón siguiente - Clases: {clases}')
                print(f'¿Está deshabilitado?: {esta_deshabilitado}')
                
                if not esta_deshabilitado and boton_siguiente.is_enabled():
                    print('Avanzando a la siguiente página...')
                    boton_siguiente.click()
                    time.sleep(1)
                else:
                    print('Botón siguiente deshabilitado - No hay más páginas')
                    break
            else:
                print('No se encontró botón siguiente - Finalizando búsqueda')
                break
        
        if lista_botones_observados:
            print(f'\nTotal de observaciones encontradas: {len(lista_botones_observados)}')
            ultimo_observado = lista_botones_observados[-1]  
            print(f'Descargando el último observado: Página {ultimo_observado["pagina"]}, Fila {ultimo_observado["fila"]}')
            
            # Navegar a la página correcta si es necesario
            if ultimo_observado['pagina'] < cont:
                print(f'Navegando de regreso a la página {ultimo_observado["pagina"]}...')
                
                # Ir a la primera página
                boton_primera_pagina = driver.find_elements(By.CSS_SELECTOR, 'body > div:nth-child(3) > div.col-sm-9 > div > div.nav-div > div > pagination-controls > pagination-template > ul > li:nth-child(3) > a')
                if boton_primera_pagina:
                    boton_primera_pagina[0].click()
                    time.sleep(1)
                    print('Regresado a página 1')
                
                # Avanzar hasta la página del último observado
                pagina_actual = 1
                while pagina_actual < ultimo_observado['pagina']:
                    boton_sig = driver.find_element(By.CSS_SELECTOR, 'body > div:nth-child(3) > div.col-sm-9 > div > div.nav-div > div > pagination-controls > pagination-template > ul > li.pagination-next.ng-star-inserted')
                    if boton_sig.is_enabled():
                        boton_sig.click()
                        time.sleep(1)
                        pagina_actual += 1
                        print(f'Avanzando a página {pagina_actual}')
                    else:
                        break
                
                print(f'Llegamos a la página {ultimo_observado["pagina"]}')
            
            # Hacer click en el botón de descarga del último observado
            print('Buscando el botón de descarga...')
            boton_descarga_final = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ultimo_observado['selector']))
            )
            
            # Hacer scroll al elemento para que sea visible
            print('Haciendo scroll al botón...')
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_descarga_final)
            time.sleep(1)
            
            # Esperar a que sea clickable
            boton_descarga_final = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ultimo_observado['selector']))
            )
            
            print('Haciendo click en el botón de descarga...')
            try:
                boton_descarga_final.click()
            except:
                # Si falla el click normal, usar JavaScript click
                print('Click normal falló, usando JavaScript click...')
                driver.execute_script("arguments[0].click();", boton_descarga_final)
            
            time.sleep(2)
            respuesta=mover_archivos(ruta_descargas,ruta_carpeta,'ESQUELA_OBSERVACION')
            if respuesta:return True
            else: return False
        else:
            print('No se encontraron observaciones en ninguna página')
            return False

    except Exception as e:
        print(f'ERROR EN DESCARGA DE OBSERVADOS: {e}')
        #print(f'Tipo de error: {type(e).__name__}')
        traceback.print_exc()
        return False

def tachados_siguelo(historial:Logger,registro):
    with open(RUTA_TACHADO,'r') as file:
        tachados=json.load(file)
    inmatriculacion=registro['inmatriculacion']
    if inmatriculacion in tachados:historial.info(f'El correo del titulo {registro["titulo"]} fue enviado anteriormente')
    else:
        historial.obs(f'Inicio del envio del correo de tacha del titulo {registro['titulo']}')
        body={"inmatriculacion":inmatriculacion,"tipo":3}
        asesores=obtener_asesores_asociados(body,historial)
        inmatriculacion_compania=asesores['tramite_compania']
        to_s_autohub='jmallqui@autohub.pe,asistente@autohub.pe,administracion@autohub.pe'
        subject=f"AUTOHUB: Inmatriculación N° {inmatriculacion_compania} - TACHADO"
        mensaje=generar_html_autohub("tacho",inmatriculacion_compania,registro['kardex'],registro['titulo'],registro['anio'])
        enviar_correo(to_s_autohub,subject,mensaje,2,'','','',historial,html=True)
        tachados[inmatriculacion]=True
        with open(RUTA_TACHADO,'w') as file:
            json.dump(tachados,file,indent=4)
        historial.info(f'Correo de tacha enviado para el titulo {registro["titulo"]}')

def consultar_estado(driver:WebDriver,registro,ruta_descargas,historial:Logger,contador):
    try:
        estado_siguelo=''
        contador_inscripcion=1

        #SE OBTIENE EL ESTADO DEL TITULO EN EL SIGUELO
        WebDriverWait(driver,5).until(EC.presence_of_element_located((By.CSS_SELECTOR,"body > div:nth-child(11) > div.col-sm-6 > div > div:nth-child(1)")))
        estado_siguelo=driver.find_element(By.CSS_SELECTOR,'body > div:nth-child(11) > div.col-sm-6 > div > div:nth-child(1)').get_attribute('innerText')
        estado_siguelo=estado_siguelo.upper().strip()
        historial.info(f'Estado del titulo: {estado_siguelo}')
        enviar_estado_siguelo(historial,estado_siguelo,registro['inmatriculacion'])

        #ACCIONES DEPENDIENDO DE LOS ESTADOS
        if estado_siguelo in ['OBSERVADO','SUSPENDIDO']:estado_siguelo='OBSERVADO'
        match estado_siguelo:
            case 'INSCRITO':
                historial.title(f'Iniciando con la descarga de los documentos del titulo {registro["titulo"]} que se encuentra inscrito')
                registro['estadosiguelo']=estado_siguelo
                descargar_documentos_inscripcion(historial,driver,registro,ruta_descargas,contador,contador_inscripcion)
                estado_inscrito(historial,registro)
            case 'OBSERVADO':
                if registro['estadosiguelo'] and registro['estadosiguelo']=='OBSERVADO' and registro['estadosiguelo']==estado_siguelo:
                    historial.obs('Este titulo ya fue observado anteriormente')
                else:
                    historial.title(f'Iniciando con la descarga de los documentos del titulo {registro["titulo"]} que se encuentra observado')
                    pass
                    registro['estadosiguelo']=estado_siguelo
                    if not descargar_documentos_observados(driver,registro,ruta_descargas):raise Exception('Fallo al descargar la esquela de observacion')
                    estado_observado(historial,registro)
            case 'LIQUIDADO':
                historial.title(f'Iniciando con la descarga de los documentos del titulo {registro["titulo"]} que se encuentra liquidado')
            case 'TACHADO':
                historial.title(f'Iniciando con la descarga de los documentos del titulo {registro["titulo"]} que se encuentra tachado')
                tachados_siguelo(historial,registro)
            case 'REINGRESADO':
                historial.title(f'Iniciando con la descarga de los documentos del titulo {registro["titulo"]} que se encuentra reingresado')
                if registro['estadosiguelo']=='REINGRESADO' and registro['estadosiguelo']==estado_siguelo:historial.info('Este titulo ya fue reingresado anteriormente')
                else:registro['reingresado']='SI'
                estado_reingresado(historial,registro)
            case _:
                resp,dias_habiles=calcular_dias_habiles(registro['fecha_presentacion'])
                if resp:
                    enviar_reclamo=reclamos(historial,registro)
                    if enviar_reclamo and 'reclamo' in enviar_reclamo and enviar_reclamo['reclamo'] == 'S':
                        historial.obs(f'El titulo {registro['titulo']} ha pasado los 7 dias habiles:  {dias_habiles} dias, se procedera con el reclamo')
                        kardex=''
                        if registro['kardex']=='ERROR' and registro['kardex']=='':kardex=''
                        else:kardex=registro['kardex'] 
                        asunto=f'RECLAMO TITULO {registro['anio']} - {registro['titulo']} / K-{kardex}'
                        mensaje_autohub=generar_html_reclamos(registro['fecha_presentacion'],registro['titulo'],registro['anio'],registro['oficina'])
                        destinatario_cco=''
                        if 'co' in enviar_reclamo:destinatario_cco=enviar_reclamo['co']
                        enviar_correo(CORREOS_RECLAMOS,asunto,mensaje_autohub,2,'',destinatario_cco,'',historial,html=True)
                else: pass
                historial.obs('Estado del siguelo que no procesable')
                time.sleep(2)
        #driver.find_element(By.CSS_SELECTOR,'body > app-navigation > nav > button').click()
        time.sleep(1)
        #driver.find_element(By.CSS_SELECTOR,'#navbarSupportedContent>ul>li:nth-child(3)').click()
        #driver.find_element(By.CSS_SELECTOR,'#navbarSupportedContent > ul > li:nth-child(3) > a)').click()
    except Exception as e:
        historial.error(f'Fallo en la consulta del estado en siguelo . {registro['observacion'] if 'observacion' in registro else '' }: {e}')
        driver.get('https://sigueloplus.sunarp.gob.pe/siguelo/')
        raise Exception(e)
def proceso_siguelo(registro,historial:Logger,driver:WebDriver,ruta_descargas,contador):
    try:
        if not verificar_conexion(historial):
            historial.obs(f'Se excedio la hora de consulta .... se va a cerrar el programa')
            sys.exit()
        driver.refresh()
        login_siguelo(historial,registro,driver)
        consultar_estado(driver,registro,ruta_descargas,historial,contador)
        return True
    except Exception as e:
        actualizar_bitacora(registro)
        intentos=obtener_contador_intentos(registro['inmatriculacion'])
        if intentos==2:enviar_webhoook(f'ERROR BOT SIGUELO - {os.getenv('BOT_ASIGNADO')}',"URGENTE",f'Error en la consulta del titulo {registro["titulo"]} - {COMPANIAS[registro['compania']] if registro['compania']  in COMPANIAS else "NUEVA COMPANIA"} ',f"{e}")
        #traceback.print_exc()
        historial.error(f"error proceso siguelo. {e}")
        driver.get('https://sigueloplus.sunarp.gob.pe/siguelo/')
        if registro['estadosiguelo']=='INSCRITO':
            registro['estado']='INCOMPLETO'
            return True
        return False

        