import time
import os
from camoufox.sync_api import Camoufox
from playwright.sync_api import Page, BrowserContext
from utils.funciones import convertir_png_pdf
from resources.datosfijos import *
from utils.logger import Logger
from bot.SUNARP.Sprl_Sid.sid import proceso_sid
def login_sprl(page:Page,historial:Logger):
    try:
        page.goto('https://sprl.sunarp.gob.pe/sprl/ingreso',wait_until='networkidle')
        time.sleep(3)
        try:page.locator('#cdk-overlay-0 > nz-modal-container > div > div > button').click(timeout=3000)
        #try:page.locator('body > app-root > app-iniciar-sesion > nz-layout > div:nth-child(2) > div > div.backgroundSunarp > div > div > app-campo-login > nz-layout > div > div > nz-form-item > div.backgroundLogin.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-10.ant-col-lg-10.ant-col-xl-10 > div > div > div > app-card-glass > div > nz-content:nth-child(4) > form > nz-form-item > nz-form-control > div > div > div > button').click(timeout=3000)
        except:pass
        with page.expect_navigation(wait_until='networkidle'):
            page.locator('body > app-root > app-iniciar-sesion > nz-layout > div:nth-child(2) > div > div.backgroundSunarp > div > div > app-campo-login > nz-layout > div > div > nz-form-item > div.backgroundLogin.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-10.ant-col-lg-10.ant-col-xl-10 > div > div > div > app-card-glass > div > nz-content:nth-child(4) > form > nz-form-item > nz-form-control > div > div > div > button').click()
        time.sleep(4)
        logo=page.query_selector('body > app-root > app-main > nz-layout > nz-row > div:nth-child(2) > p:nth-child(2)')
        if not logo:
            time.sleep(2)
            user='JPAINOSC001'
            pwd='GIULI0215'
            page.locator('#l-login > div:nth-child(5) > div > input').fill(user)
            time.sleep(1)
            page.locator('#l-login > div:nth-child(6) > div > input').fill(pwd)
            time.sleep(1)
            with page.expect_navigation(wait_until='networkidle'):
                page.locator('#l-login > div:nth-child(8) > button').click()
            time.sleep(3)
            return True
        else: return True
    except Exception as e:
        historial.error(f'Error en el Login al sprl. {e}')
        return False
def descargar_pdf_observacion(page:Page,registro:dict,historial:Logger):
    try:
        ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{registro['titulo']}-{registro['anio']}')
        os.makedirs(ruta_carpeta, exist_ok=True)
        rutaimg=os.path.join(ruta_carpeta,'esquela_observacion.png')
        ruta_pdf=os.path.join(ruta_carpeta,f'ESQUELA_OBSERVACION_{registro['titulo']}.pdf')
        historial.obs('Iniciando con la descarga del documento de la observacion')
        page.locator('body > app-root > app-main > nz-layout > nz-layout > nz-content > detalle-titulo > div > nz-spin > div > div:nth-child(3) > div > nz-table > nz-spin > div > div > nz-table-inner-default > div > table > tbody > tr:nth-child(2) > td.th2.ant-table-cell > a').click()
        time.sleep(6)
        page.wait_for_selector('#viewer > div > div > canvas')
        page.evaluate("""document.querySelector('body > app-root > app-main > nz-layout > nz-header').remove()""")
        time.sleep(1)
        page.evaluate("""document.querySelector('body > app-root > app-main > nz-layout > nz-row').remove()""")
        time.sleep(1)
        page.locator('#viewer > div > div > canvas').screenshot(path=rutaimg)
        historial.obs('se obtuvo la imagen de la esquela')
        convertir_png_pdf(rutaimg,ruta_pdf)
        historial.info('Se descargo la esquela de observacion')
        os.remove(rutaimg)
        historial.debug('Se elimino el archivo imagen de la esquela')
        return True
    except Exception as e:
        historial.error(f'Ocurrio un error al descargar la esquela de observacion. {e}')
        return False
def obtener_estado_sprl(page:Page,registro:dict,historial:Logger,browser:BrowserContext):
    try:
        page.goto('https://sprl.sunarp.gob.pe/sprl/main/estado-titulo-pag-liq',wait_until='load')
        time.sleep(2)
        # Realizando la consulta
        page.locator('body > app-root > app-main > nz-layout > nz-layout > nz-content > app-estado-titulo-pag-liq > div > div.card-list-body > div > div > nz-content > nz-spin > div > nz-card.ant-card.ant-card-bordered.ng-star-inserted > div > form > div > div > app-select-custom > div > div.ant-col.ant-col-xs-24.ant-col-sm-24.ant-col-md-23.ant-col-lg-23.ant-col-xl-23.ng-untouched.ng-pristine.ng-valid > nz-form-item > nz-form-control > div > div > nz-select > nz-select-top-control > nz-select-item').click()
        page.wait_for_selector('#cdk-overlay-0 > nz-option-container > div > cdk-virtual-scroll-viewport')
        page.keyboard.type(registro['oficina'])
        page.click(f'text="{str(registro['oficina'])}"')
        page.click('body > app-root > app-main > nz-layout > nz-layout > nz-content > app-estado-titulo-pag-liq > div > div.card-list-body > div > div > nz-content > nz-spin > div > nz-card:nth-child(3) > div.ant-card-body > form > app-select-input-custom > nz-row > nz-col:nth-child(1) > nz-form-item > nz-form-control > div > div > nz-select > nz-select-top-control > nz-select-item')
        page.click(f'text="{str(registro['anio'])}"')
        page.click("body > app-root > app-main > nz-layout > nz-layout > nz-content > app-estado-titulo-pag-liq > div > div.card-list-body > div > div > nz-content > nz-spin > div > nz-card:nth-child(3) > div.ant-card-body > form > app-select-input-custom > nz-row > nz-col:nth-child(2) > nz-form-item > nz-form-control > div > div > input")
        page.keyboard.type(registro['titulo'])
        # Click en el botón de buscar
        page.click("body > app-root > app-main > nz-layout > nz-layout > nz-content > app-estado-titulo-pag-liq > div > div.card-list-body > div > div > nz-content > nz-spin > div > nz-card:nth-child(3) > div.ant-card-body > form > div > app-button > div > div > button")
        historial.obs('Esperando que figuren los datos')
        page.wait_for_selector('body > app-root > app-main > nz-layout > nz-layout > nz-content > detalle-titulo > div > nz-spin > div > div:nth-child(1) > div > nz-table > nz-spin > div > div > nz-table-inner-default > div > table > tbody > tr.ant-table-row > td:nth-child(2) > strong',timeout=60000)
        respuesta=page.query_selector('body > app-root > app-main > nz-layout > nz-layout > nz-content > detalle-titulo > div > nz-spin > div > div:nth-child(3) > div > nz-table > nz-spin > div > div > nz-table-inner-default > div > table > tbody > tr:nth-child(2) > td.th2.ant-table-cell')
        if respuesta:texto_completo=page.locator('body > app-root > app-main > nz-layout > nz-layout > nz-content > detalle-titulo > div > nz-spin > div > div:nth-child(3) > div > nz-table > nz-spin > div > div > nz-table-inner-default > div > table > tbody > tr:nth-child(2) > td.th2.ant-table-cell').inner_text()
        else:texto_completo=page.locator('body > app-root > app-main > nz-layout > nz-layout > nz-content > detalle-titulo > div > nz-spin > div > div:nth-child(2) > div > nz-table > nz-spin > div > div > nz-table-inner-default > div > table > tbody > tr:nth-child(1) > td.th2.ant-table-cell').inner_text()
        texto=texto_completo.split(' ')[0]
        if texto.upper()=='EN': texto=texto+' '+texto_completo.split(' ')[1]
        historial.info(f'Estado del titulo: {texto}')
        time.sleep(2)
        if registro['estadosiguelo']=='OBSERVADO' and registro['estadosiguelo']==texto:historial.info('Este titulo ya fue observado anteriormente')
        else: 
            if texto =='OBSERVADO':
                if not proceso_sid(historial,registro,browser): return False
        registro['estadosiguelo']=texto 
        return True
    except Exception as e:
        historial.error(f'Error al obtener el estado del sprl {e}')
        return False
def consulta_sprl(historial:Logger,registro:dict):
    with Camoufox(headless=True) as browser:
        page=browser.new_page()
        if not login_sprl(page,historial):
            page.close() 
            return False
        if not obtener_estado_sprl(page,registro,historial, browser):
            page.close()
            return False
        page.close()
        return True