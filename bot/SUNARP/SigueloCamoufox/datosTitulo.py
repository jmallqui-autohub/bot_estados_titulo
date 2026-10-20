import os
import base64
import shutil
import time as tiempo
from playwright.sync_api import Page
from utils.logger import Logger
from resources.datosfijos import *
from resources.inmatriculacion import Inmatriculacion
from utils.html import *
from utils.funciones import *
from middleware.funciones_correo import *
from middleware.apis import *

def descargar_documentos_inscripcion(historial: Logger, page: Page, registro:Inmatriculacion):
    # Creacion del directorio donde se guardara los documentos descargados
    ruta_carpeta = os.path.join(RUTAPRIN, 'download', f'{registro.titulo}-{registro.anio}')
    os.makedirs(ruta_carpeta, exist_ok=True)

    valor=0
    # verificadores de los documentos
    asiento=True
    tive=True
    ordenGiro=True
    anotacion=True
    nroPlaca=True

    try:
        # Verificamos si figuran todos los campos en la tabla para iniciar con la descargas
        ruta_anotacion=os.path.join(ruta_carpeta, f'{registro.titulo}_ANOTACION.pdf')

        # Descarga de la anotacion
        try:
            if not os.path.exists(ruta_anotacion) and anotacion:
                with page.expect_download(timeout=15000) as download_info:
                    page.locator("body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(5) > td > a > span").click()
                download_info.value.save_as(ruta_anotacion)
                historial.info('Anotacion descargada')
                tiempo.sleep(1)
            else: historial.info(f'La anotacion fue descargada anteriormente')
        except Exception as e:
            historial.error('Fallo la descarga de la anotacion')
            enviar_seguimiento(historial,registro,'error-descargar-anotacion')
            raise Exception(f'Fallo la descarga de la anotacion: {e}')
        tiempo.sleep(2)
        page.locator("body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(4) > td > a > span").click()
        tiempo.sleep(2)
        if page.locator("#mat-dialog-1 > app-partidas > mat-card-content > div > div > table > thead > tr:nth-child(2)").count()>0: valor=1
        tiempo.sleep(2)
        page.wait_for_selector(f"#mat-dialog-{valor} > app-partidas > mat-card-content > div > div > table > thead > tr:nth-child(2)",timeout=60000)
        nro_etiquetas = page.locator(f"#mat-dialog-{valor} > app-partidas > mat-card-content > div > div > table > thead > tr:nth-child(2)>td").count()
        historial.info(f'Nro de campos encontrados: {nro_etiquetas}')

        if nro_etiquetas <6:
            historial.obs('Verificando que campo falta')
            faltantes=[]
            lista_etiquetas=page.locator(f'#mat-dialog-{valor} > app-partidas > mat-card-content > div > div > table > thead > tr:nth-child(2)>td').all_inner_texts()
            for index,etiqueta in enumerate(LISTA_CABECERA_TITULO):
                if index ==0:continue
                if etiqueta.strip() not in lista_etiquetas: faltantes.append(etiqueta.strip())
            historial.obs(f'Faltan los siguientes campos: {', '.join(faltantes)}')
            if registro.titulo_tipo == "P":
                registro.observacion=f'Faltan los siguientes campos: {', '.join(faltantes)} para completar la descarga de los documentos en el siguelo.'
                imagen_bytes = page.screenshot()
                imagen_b64 = base64.b64encode(imagen_bytes).decode('utf-8')
                html=generar_html_errores_siguelo(imagen_b64,registro)
                enviar_correo(CORREOS_ERROR, f"Error Inscripcion - Faltan documentos en SUNARP (TITULO {registro.titulo})", html, 1, '', '', '', historial, html=True)
                page.locator(f'#mat-dialog-{valor} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
                raise Exception('Faltan campos para la descarga de documentos')
            else:
                for faltante in faltantes:
                    if faltante =="Asientos": asiento=False
                    if faltante =="TIVe": tive=False
                    if faltante =="O.Giro": ordenGiro=False
                    if faltante =="Placa": nroPlaca=False

        # Se procede a obtener los datos y la descarga de documentos
        historial.info(f"Se procede con la obtencion de los datos y descargas de los documentos de la {'inscripcion' if registro.titulo_tipo == 'P' else 'rectificacion'}")
        tiempo.sleep(3)

        ### Se obtiene la placa del vehiculo
        if nroPlaca:
            placa = page.locator(f'#mat-dialog-{valor} > app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(4)').inner_text().upper().strip()
            historial.obs(f'la placa {placa}')
            registro.placa = placa
        

        # rutas de los archivos a descargar
        ruta_asiento=os.path.join(ruta_carpeta,f'{registro.titulo}.pdf')
        ruta_tive=os.path.join(ruta_carpeta,f'{registro.titulo}_TIVE.pdf')
        ruta_orden_giro = os.path.join(ruta_carpeta, f'{registro.titulo}_ORDEN_GIRO.pdf')

        ### Descarga del Asiento de inscripcion
        try:
            if not os.path.exists(ruta_asiento) and asiento:
                try:
                    with page.expect_download(timeout=60000) as download_info:
                        page.locator(f'#mat-dialog-{valor}> app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(3)').click()
                    download = download_info.value
                except Exception as t:
                    historial.obs(f'Se intentara la descarga del asiento nuevamente')
                    # Cierra el modal
                    page.locator(f'#mat-dialog-{valor} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
                    tiempo.sleep(2)
                    # Se abra nuevamente el modal
                    page.locator("body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(4) > td > a > span").click()
                    tiempo.sleep(3)
                    # Se intenta la descarga nuevamente
                    if page.locator("#mat-dialog-1 > app-partidas > mat-card-content > div > div > table > thead > tr:nth-child(2)").count()>0: valor=1
                    tiempo.sleep(1)
                    with page.expect_download(timeout=60000) as download_info:
                        page.locator(f'#mat-dialog-{valor}> app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(3)').click()
                    download = download_info.value
                download.save_as(ruta_asiento)
                historial.info('Se descargo el asiento de inscripcion')
                
            else: historial.info('El asiento de inscripcion fue cargado anteriormente o es un caso de recti y no se encuentra el campo')
        except Exception as e:
            registro.observacion = 'Fallo al descargar del Asiento de inscripcion'
            historial.error(f'Fallo en la descarga del asiento de inscripcion {e}')
            page.locator(f'#mat-dialog-{valor} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
            enviar_seguimiento(historial,registro,'error-descargar-inscripcion',f'Fallo en la descarga del asiento de inscripcion {e}')
            raise Exception('Fallo la descarga del Asiento de inscripcion')
        tiempo.sleep(2)
        if not nroPlaca and registro.titulo_tipo =="R":
            placa=obtener_datos_inscripcionV2(historial,ruta_asiento)
            if placa:
                historial.obs(f'la placa {placa}')
                registro.placa = placa
            else: raise Exception('No se obtuvo el nro de placa')               
        #### Se valida el codigo de verificacion
        if not registro.codigo_verificacion or str(registro.codigo_verificacion).upper() in ['FALSE', 'FALSO'] or len(registro.codigo_verificacion) != 8:
            registro.observacion='el codigo de verificacion no es valido verificar'
            registro.intento=2
            raise Exception('Codigo de verificacion no valido para la consulta. Verificar')
        
        ### Descarga de la tive
        try:
            if not os.path.exists(ruta_tive) and tive:
                page.locator(f"#mat-dialog-{valor} > app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(5) > button").click()
                page.wait_for_selector('#swal2-content > p > b', timeout=10000)
                ##### Se registra la placa
                page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-content > input.swal2-input').press_sequentially(registro.placa,delay=500)
                tiempo.sleep(1)
                page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled').click()
                tiempo.sleep(1)
                ####  Se registra el codigo de verificacion
                page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-content > input.swal2-input').press_sequentially(registro.codigo_verificacion,delay=500)
                tiempo.sleep(1)
                with page.expect_download(timeout=15000) as download_info:
                    page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled').click()
                download = download_info.value
                download.save_as(ruta_tive)
                historial.info('Se descargo la tive')
            else: historial.info('La TIVE ya fue descargada anteriormente o es un caso de recti y no se encuentra el campo')
        except Exception as e:
            registro.observacion = f'Fallo al descargar la tive.{e}'
            historial.error(f'Fallo la descarga de la tive:{e}')
            page.locator(f'#mat-dialog-{valor} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
            enviar_seguimiento(historial,registro,'error-descargar-tive',registro.observacion)
            raise Exception('Fallo la descarga de la tive')
        tiempo.sleep(2)
        ### Descarga de la orden de giro
        try:
            if not os.path.exists(ruta_orden_giro) and ordenGiro:
                page.locator(f"#mat-dialog-{valor} > app-partidas > mat-card-content > div > div > table > tbody > tr > td:nth-child(6) > button").click()
                page.wait_for_selector('#swal2-content > p > b', timeout=10000)
                ##### Se registra la placa
                page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-content > input.swal2-input').press_sequentially(registro.placa,delay=500)
                tiempo.sleep(1)
                page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled').click()
                tiempo.sleep(1)
                #### Se registra el codigo de verificacion
                page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-content > input.swal2-input').press_sequentially(registro.codigo_verificacion,delay=500)
                tiempo.sleep(1)
                page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled').click()
                tiempo.sleep(1)
                try:
                    with page.expect_download(timeout=120000) as download_info:
                        page.locator('body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled').click()
                    download = download_info.value
                    download.save_as(ruta_orden_giro)
                    historial.info('Se descargo la orden de giro')
                except Exception:
                    mensaje = page.locator('#swal2-content > table > tbody > tr > td > p').inner_text().strip()
                    registro.observacion=mensaje
                    historial.obs(mensaje)
                    historial.obs('Se procedera a reemplazar la orden de giro con un doc en blanco para continuar el proceso')
                    ruta_archivo_blanco=os.path.join(RUTAPRIN,'resources','docenblanco.pdf')
                    shutil.copy2(ruta_archivo_blanco,ruta_orden_giro)
                    historial.info('Se copio el archivo')
                    registro.orden_giro=False
                    tiempo.sleep(1)
                    page.keyboard.press("Escape")
            else:historial.info('La orden de giro ya fue descargado anteriormente o es un caso de recti y no se encuentra el campo')   
        except Exception as e:
            enviar_seguimiento(historial,registro,'error-descargar-ogiro',f'Fallo la descarga de la orden de giro:{e}')
            raise Exception(f'Fallo la descarga de la orden de giro:{e}')
        tiempo.sleep(3)
        # Cerramos el modal
        page.locator(f'#mat-dialog-{valor} > app-partidas > mat-card-header > mat-toolbar > mat-icon').click()
        tiempo.sleep(3)
        historial.info(f'Se descargaron todos los documentos de la {"inscripcion"if registro.titulo_tipo == "P" else "rectificacion"}')
        enviar_seguimiento(historial,registro,'descarga-documento')
    except Exception as e:
        raise Exception(e)


