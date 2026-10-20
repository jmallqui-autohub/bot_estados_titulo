import os
import time
import base64 
from utils.logger import Logger
from utils.images_to_pdf import imagesB64_to_pdfB64
from playwright.sync_api import BrowserContext,Page
from resources.datosfijos import *
def login_sid(historial:Logger,page:Page):
    usuario=os.getenv('USER_SID')
    contrasena=os.getenv('PASSWORD_SID')
    try:
        page.locator('#user').fill(usuario)
        time.sleep(1)
        page.locator('#pass').fill(contrasena)
        time.sleep(1)
        page.locator('#frmLogin > table > tbody > tr > td > table > tbody > tr:nth-child(4) > td > table > tbody > tr:nth-child(3) > td:nth-child(2) > input').click()
        page.wait_for_url("https://sid.sunarp.gob.pe/sid/login.htm",timeout=10000)
        time.sleep(1)
        page.locator("#imagen4 > img").click()
        time.sleep(1)
        page.wait_for_url("https://sid.sunarp.gob.pe/sid/bandeja.htm?method=buscarObservados",timeout=10000)
        time.sleep(1)
        return True
    except Exception as e:
        historial.error(f'Error en el login de Sid Sunarp. {e}')
        return False
def consulta_titulo(historial:Logger, page:Page, registro:dict):
    try:
        titulo=registro['titulo']
        anio=registro['anio']
        if len(titulo)<8:
            cont=8-len(titulo)
            for i in range(cont):
                titulo='0'+titulo
        page.locator('#anioTitulo').select_option(value=anio)
        time.sleep(1)
        page.locator('#nroTitulo').fill(titulo)
        time.sleep(1)
        page.locator('#form_buscarObs > div:nth-child(9) > button').click()
        time.sleep(5)
        page.locator('#form_buscarObs > div:nth-child(9) > button').click()
        tablas=page.query_selector('#row')
        cuerpo=tablas.query_selector('tbody')
        filas=cuerpo.query_selector_all('tr')
        celdas=filas[0].query_selector_all('td')
        if len(celdas)>1:
            with page.context.expect_page() as new_page_info:
                        celdas[10].click()
            esquela_page = new_page_info.value
                    

            #Pagina de Esquelas
            esquela_page.wait_for_load_state('networkidle')
            
            images = []
            
            imagen = esquela_page.query_selector(r'#frmEsquela\:imagenEsquela')
            screenShoot = imagen.screenshot()                          
            last_b64 = base64.b64encode(screenShoot).decode('utf-8')
            images.append(last_b64)
            
            repetir = True

            while repetir:
                with esquela_page.expect_navigation():
                    esquela_page.click(r"#frmEsquela\:j_id547563102_20a32719 > span.ui-button-text.ui-c")
                    
                esquela_page.wait_for_timeout(500)
                imagen = esquela_page.query_selector(r'#frmEsquela\:imagenEsquela')
                screenShoot = imagen.screenshot()
                
                sb64 = base64.b64encode(screenShoot).decode('utf-8')
                if sb64 == last_b64:                        
                    repetir = False
                else:
                    images.append(sb64)
                    last_b64 = sb64

            
            for _ in range(1, len(images)):
                with esquela_page.expect_navigation():
                    esquela_page.click(r"#frmEsquela\:j_id547563102_20a32766 > span.ui-button-icon-left.ui-icon.ui-c.ui-icon-carat-1-w")

            pdf_base64 = imagesB64_to_pdfB64(images)
            esquela_page.close()
            return pdf_base64
    except Exception as e:
        historial.error(f'Error en la consulta del Sid Sunarp. {e}')
        return False

def proceso_sid(historial:Logger, registro:dict,browser:BrowserContext):
    page2=browser.new_page()
    page2.goto("https://sid.sunarp.gob.pe/sid/sesion.htm",wait_until='load')
    time.sleep(2)
    historial.title('Buscando el documento de observacion en SID SUNARP')
    if not login_sid(historial,page2): return False
    doc_base64=consulta_titulo(historial,page2,registro)
    if not doc_base64:return False
    ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{registro['titulo']}-{registro['anio']}')
    os.makedirs(ruta_carpeta, exist_ok=True)
    ruta_pdf=os.path.join(ruta_carpeta,f'ESQUELA_OBSERVACION_{registro['titulo']}.pdf')
    with open(ruta_pdf,'wb') as f:
        f.write(base64.b64decode(doc_base64))
    historial.info('Se descargo la esquela de observacion')
    page2.close()
    return True


