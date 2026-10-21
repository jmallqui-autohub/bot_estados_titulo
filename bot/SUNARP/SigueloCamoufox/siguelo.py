import os
import time
import traceback
import sys
import json
import contextlib
from camoufox.sync_api import Camoufox
from playwright.sync_api import Page, BrowserContext, TimeoutError as PlaywrightTimeError
from pathlib import Path
from utils.logger import Logger
from utils.funciones import *
from resources.datosfijos import *
from resources.inmatriculacion import Inmatriculacion
from middleware.funciones_correo import *
from middleware.apis import *
from bot.LECTURAPDF.estados_funciones import *
from utils.html import *
from bot.SUNARP.SigueloCamoufox.datosTitulo import descargar_documentos_inscripcion
from bot.SUNARP.SigueloCamoufox.detalleSeguimiento import *
from bot.OPCLOUD.opcloud import actualizar_opencloud


def login_siguelo(historial: Logger, registro:Inmatriculacion, page:Page,browser: BrowserContext):
    try:
        # Se navega a la pagina del Siguelo
        url=os.getenv('URL_SIGUELO')
        page.goto(url, wait_until='domcontentloaded', timeout=10000)
        historial.debug('Cargo la pagina del siguelo')
        
        # Se verifica nuevo poppup
        try:
            if page.locator('.promo-close').is_visible(timeout=3000):
                page.click('#btnCerraAsistente')
                page.click('#mat-dialog-0 > div > button')
                historial.debug('Se cerro el popup')
        except Exception:
            pass

        # Se verifica si existe el popup de comunicados
        try:
            if page.locator('#mat-dialog-0 > mat-dialog-actions > button:nth-child(2)').is_visible(timeout=3000):
                page.click('#mat-dialog-0 > mat-dialog-actions > button:nth-child(2)')
                historial.debug('Se hizo click en el boton de ignorar')
        except Exception:
            pass
        time.sleep(3)

        # Se llenan los campos para la consulta
        page.locator('#cboOficina').select_option(label=registro.oficina)
        time.sleep(1)
        page.locator('#cboAnio').select_option(value=registro.anio)
        time.sleep(1)
        page.locator('#interno > div > div > form > div:nth-child(7) > div > div > input').press_sequentially(registro.titulo,delay=500)
        time.sleep(5)
        page.locator('#interno > div > div > form > div:nth-child(10) > div > div > button').click()
        time.sleep(2)

        # Verificamos si existe un popup por error de algun dato
        if page.locator('#swal2-content > p').is_visible():
            mensaje_popup=page.locator('#swal2-content > p').inner_text()
            if mensaje_popup and mensaje_popup in LISTA_MENSAJES_SIGUELO:
                historial.obs(f'mensaje encontrado: {mensaje_popup}')
                page.reload()
                time.sleep(2)
                if registro.inicio_sesion == 0 :
                    registro.inicio_sesion=1
                    return login_siguelo(historial,registro,page,browser)
                else:
                    historial.obs(f'El sistema no esta enviando algun dato que se requiere de la consulta.')
                    registro.observacion=f'Faltan datos de la consulta'
                    raise Exception('Faltan datos de la consulta')

        # Verificamos si existe el popup de baneo
        if page.locator('#swal2-content > table > tfoot > tr > td').is_visible():
            mensaje_popup=page.locator('#swal2-content > table > tfoot > tr > td').inner_text().strip()
            if mensaje_popup and mensaje_popup =='429':
                historial.info(f'Mensaje de error encontrado: {mensaje_popup}, se detecto que el bot se encuentra baneado, detiene el proceso de consultas de bot hasta la respuesta del usuario')
                notificar_bot(historial,registro)
                respuesta_usuario = pausar_bot(historial)
                if respuesta_usuario:
                    page.reload()
                    return login_siguelo(historial, registro, page,browser)
                else:
                    historial.info('No hubo respuesta del usuario se procede al cierre del bot ')
                    enviar_webhoook(f'BOT-{os.getenv("BOT_ASIGNADO")}', 'URGENTE', 'Estado del bot', 'No hubo respuesta del usuario para continuar con el proceso del bot, se procede al cierre del bot')
                    sys.exit()

            if mensaje_popup and mensaje_popup == '0002':
                historial.obs(f"Mensaje de error encontrado: {mensaje_popup}, Error en los datos de la consulta")
                registro.observacion=f'Error en los datos de la consulta {registro.interno}'
                raise Exception('Error en los datos de la consulta')

        # Se espera que cargue la bandeja de la consulta
        time.sleep(2)
        page.wait_for_selector("body > div:nth-child(6) > div:nth-child(2) > div > input", timeout=120000)
        time.sleep(2)
        return page
    except PlaywrightTimeError as t:
        historial.error(f'Demoro mucho la carga del siguelo.{t}')
        if registro.inicio_sesion==0:
            historial.obs('Se intentara un segundo intendo de login')
            page.close()
            time.sleep(2)
            registro.inicio_sesion=1
            page=browser.new_page()
            return login_siguelo(historial,registro,page,browser)
        else:
            registro.observacion=f'Fallo en el login del siguelo.{t}'
            enviar_seguimiento(historial,registro,'error-pagina-sunarp',registro.observacion)
            historial.error(f'{registro.observacion}')
            return page
    except Exception as e:
        registro.observacion=f'Fallo en el login del siguelo {e}'
        enviar_seguimiento(historial,registro,'error-pagina-sunarp',registro.observacion)
        historial.error(f'{registro.observacion}')
        if registro.inicio_sesion==0:registro.inicio_sesion=1
        return page

def consultar_estado(page:Page, registro:Inmatriculacion, historial: Logger):
    try:
        estado_siguelo = ''
        # Se obtiene el estado del titulo en el Siguelo
        estado_siguelo=page.locator("body > div:nth-child(11) > div.col-sm-6 > div > div:nth-child(1)").inner_text().upper().strip()
        historial.info(f'Estado del titulo: {estado_siguelo}')
        if estado_siguelo in ['OBSERVADO', 'SUSPENDIDO']:estado_siguelo = 'OBSERVADO'
        enviar_estado_siguelo(historial, estado_siguelo, registro)
        enviar_seguimiento(historial,registro,'obtiene-estado')
        registro.observacion=f'Estado Siguelo: {estado_siguelo}'

        # Se evalua el estado y se realiza la accion
        match estado_siguelo:
            case 'INSCRITO':
                if registro.estado_siguelo== registro.estado_autohub:
                    historial.obs('Este titulo ya fue inscrito anteriormente')
                    enviar_seguimiento(historial,registro,'mismo-estado',registro.observacion)
                else:
                    historial.title(f'Iniciando con la descarga de los documentos del titulo {registro.titulo} que se encuentra inscrito')
                    registro.estado_siguelo = estado_siguelo
                    enviar_seguimiento(historial,registro,'nuevo-estado',registro.observacion)
                    descargar_documentos_inscripcion(historial, page, registro)
                    descargar_esquela_fechaEstado(page, registro,historial)
                    estado_inscrito(historial, registro)
                    actualizar_opencloud(historial,registro)
            case 'OBSERVADO':
                if registro.estado_siguelo== registro.estado_autohub:
                    historial.obs('Este titulo ya fue observado anteriormente')
                    enviar_seguimiento(historial,registro,'mismo-estado',registro.observacion)
                else:
                    historial.title(f'Iniciando con la descarga de los documentos del titulo {registro.titulo} que se encuentra observado')
                    registro.estado_siguelo = estado_siguelo
                    enviar_seguimiento(historial,registro,'nuevo-estado',registro.observacion)
                    descargar_esquela_fechaEstado(page, registro,historial)
                    estado_observado(historial, registro)
                    actualizar_opencloud(historial,registro)
            case 'LIQUIDADO':
                if registro.estado_siguelo== registro.estado_autohub:
                    historial.obs('Este titulo ya fue liquidado anteriormente')
                    enviar_seguimiento(historial,registro,'mismo-estado',registro.observacion)
                else:
                    historial.title(f'Iniciando con la descarga de los documentos del titulo {registro.titulo} que se encuentra liquidado')
                    registro.estado_siguelo = estado_siguelo
                    enviar_seguimiento(historial,registro,'nuevo-estado',registro.observacion)
                    descargar_esquela_fechaEstado(page, registro,historial)
                    estado_liquidado(historial, registro)
                    actualizar_opencloud(historial,registro)
            case 'TACHADO':
                if registro.estado_siguelo== registro.estado_autohub:
                    historial.obs('Este titulo ya fue tachado anteriormente')
                    enviar_seguimiento(historial,registro,'mismo-estado',registro.observacion)
                else:
                    historial.title(f'Iniciando con la descarga de los documentos del titulo {registro.titulo} que se encuentra tachado')
                    registro.estado_siguelo = estado_siguelo
                    enviar_seguimiento(historial,registro,'nuevo-estado',registro.observacion)
                    descargar_esquela_fechaEstado(page, registro,historial)
                    estado_tachado(historial, registro)
                    actualizar_opencloud(historial,registro)
            case 'REINGRESADO':
                if registro.estado_siguelo== registro.estado_autohub:
                    historial.info('Este titulo ya fue reingresado anteriormente')
                    enviar_seguimiento(historial,registro,'mismo-estado',registro.observacion)
                else:
                    historial.title(f'Iniciando con la descarga de los documentos del titulo {registro.titulo} que se encuentra reingresado')
                    registro.estado_siguelo = estado_siguelo
                    enviar_seguimiento(historial,registro,'nuevo-estado',registro.observacion)
                    descargar_esquela_fechaEstado(page, registro,historial)
                    estado_reingresado(historial, registro)
                    actualizar_opencloud(historial,registro)
            case _:
                historial.obs('Estado del siguelo que no es procesable')
                registro.estado_siguelo=estado_siguelo
                enviar_seguimiento(historial,registro,'mismo-estado',registro.observacion)
                time.sleep(2)
        time.sleep(1)
    except Exception as e:
        historial.error(f'Fallo en la consulta del estado en siguelo . {registro.observacion if registro.observacion else "" }: {e}')
        page.goto('https://sigueloplus.sunarp.gob.pe/siguelo/')
        time.sleep(2)
        raise Exception(e)

def proceso_siguelo(registro:Inmatriculacion, historial: Logger, page, browser):
    try:
        if not verificar_conexion(historial):
            historial.obs('Se excedio la hora de consulta .... se va a cerrar el programa')
            sys.exit()
        page=login_siguelo(historial, registro, page, browser)
        if registro.inicio_sesion==1:raise Exception('Fallo el login del siguelo')
        enviar_seguimiento(historial,registro,'ingresa-siguelo')
        consultar_estado(page, registro, historial)
        return page
    except Exception as e:
        historial.error(f"error proceso siguelo: {e}")
        enviar_seguimiento(historial,registro,'error-general',f"error proceso siguelo: {e}")
        return page


