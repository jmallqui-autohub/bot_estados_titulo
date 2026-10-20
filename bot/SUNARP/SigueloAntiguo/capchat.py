import time
import os
import cv2
import easyocr
import numpy as np
from playwright.sync_api import Page, BrowserContext
from PIL import Image
from utils.logger import Logger
from resources.datosfijos import RUTAPRIN
def procesar_imagen_ocr(pathImg,historial:Logger):
        # Inicializar el lector
        lector = easyocr.Reader(['es']) # aqui indicamos el idioma, en este caso español.
        # Leer el texto de la imagen
        resultados = lector.readtext(pathImg)
        codigo=''
        # Imprimir los resultados
        for resultado in resultados:
            parte_codigo=resultado[1]
            codigo=codigo+parte_codigo
        codigo=codigo.replace(' ','')
        mensaje=f'el codigo es: {codigo}'
        historial.obs(mensaje)
        return codigo
def procesarImagen(pathImg,historial:Logger):
        try:
            # Carga la imagen
            img = cv2.imread(pathImg)
            # Conversión a escala de grises y binarización
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

            kernel_erode = np.ones((2,2), np.uint8)

            # Aplicar erosión antes del cierre para adelgazar primero el texto
            # kernel_erode = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            eroded = cv2.erode(binary, kernel_erode, iterations=3)

            # Filtrado y transformaciones morfológicas para limpiar el resultado
            kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, kernel_close)
                
            cv2.imwrite(pathImg, processed)
            
            return eroded
        except Exception as e:
            mensaje=f' Error al procesar la imagen. {e}'
            historial.error(mensaje)
def invertirColoresGris(pathImg,historial:Logger):
        try:
            # Invierte los colores de la imagen
            with Image.open(pathImg) as img:
                # Convertir a escala de grises si no lo está
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Invertir los valores de píxel
                inverted_img = Image.eval(img, lambda p: 255 - p)
                inverted_img.save(pathImg)
        except Exception as e:
            mensaje=f' Error al invertir los colores a gris. {e}'
            historial.error(mensaje)

def invertirColoresRGB(pathImg,historial:Logger):
        try:
            #Invierte los colores de la imagen
            with Image.open(pathImg) as img:
                r, g, b = img.split()
                rgb_image = Image.merge("RGB", (r, g, b))
                inverted_rgb_image = Image.eval(rgb_image, lambda p: 255 - p)
                #inverted_img = Image.merge("RGBA", (inverted_rgb_image.split() + (a,)))
                inverted_rgb_image.save(pathImg)
        except Exception as e:
            mensaje=f' Error al invertir los colores rgb. {e}'
            historial.error(mensaje)
def aumentarResolucion(factorDeAumentoDeResolucion,pathImg,historial:Logger):
        try:
            img = Image.open(pathImg)
            ancho_original, alto_original = img.size
            nuevo_ancho = int(ancho_original * factorDeAumentoDeResolucion)
            nuevo_alto = int(alto_original * factorDeAumentoDeResolucion)
            img = img.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
            img.save(pathImg)
        except Exception as e:
            mensaje=f'Error al aumentar la resolucion. {e}'
            historial.error(mensaje)
def extraer_code(pathImg,historial:Logger,aumenta_resol=True,invertir_colores=True):
    try:
        if aumenta_resol:aumentarResolucion(3,pathImg,historial)
        print('despues de aumentar la imagen')
        time.sleep(30)
        if invertir_colores:
            try:
                invertirColoresRGB(pathImg,historial)
            except Exception as e:
                invertirColoresGris(pathImg,historial)
        imagenProcesada = procesarImagen(pathImg,historial)
        code=procesar_imagen_ocr(pathImg,historial)
        code = code.replace(" ","")
        return code
    except Exception as e:
        print(e)
def resolverCaptcha(page:Page,historial:Logger):
    page.wait_for_selector('#textCanvas')
    imgName = 'image_captcha.png'
    pathImg = os.path.join(RUTAPRIN,'download',imgName)
    page.evaluate("""()=>{
                  var imagen = document.querySelector("#textCanvas");
                  imagen.style.filter = "blur(0px)";
                  }""") 
    time.sleep(5)   
    page.locator("#textCanvas").screenshot(path=pathImg)
    time.sleep(2)
    texto_captcha = extraer_code(pathImg,historial)
    return texto_captcha
def estadoIngresoSiguelo(page:Page,historial:Logger):
    time1 =0
    time.sleep(1)
    while time1<60:
        if page.evaluate("()=>{try{return document.querySelector('#swal2-content').textContent.toUpperCase().includes('BUSCANDO');} catch(e){return false};}"):
            time1 = time1+1
            time.sleep(0.5)
        else:
            if page.evaluate("()=>{try{return document.querySelector('#swal2-content').textContent.toUpperCase().includes('RESULTADOS CORRECTAMENTE');} catch(e){return false};}"):
                mensaje='INGRESO CORRECTAMENTE A SIGUELO'
                historial.debug(mensaje)
                return "EXITOSO"
            else:
                mensaje='Mostrando un error AL INGRESAR AL SIGUELO'
                historial.debug(mensaje)
                page.keyboard.press("Escape")
                page.keyboard.press("Escape")
                aviso = page.evaluate("()=>{try{return document.querySelector('#swal2-content').textContent.toUpperCase();} catch(e){return false};}")
                if not aviso:
                    aviso = 'El cuadro de carga se quito pero no se mostraron mas cuadros'
                    historial.obs(aviso)
                    # Refrescar la pagina de Siguelo
                    url=os.getenv('URL_SIGUELO')
                    page.goto(url,wait_until="load")
                if aviso== "EL CÓDIGO CAPTCHA ES INCORRECTO":
                    pass
                elif "SE PRODUJO UN INCONVENIENTE, POR FAVOR REVISE SU CONEXIÓN DE INTERNET." in aviso:
                    pass
                else:
                    mensaje= aviso.replace('\n','').replace('  ','')
                    historial.obs(mensaje)
                return aviso
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    mensaje='SE EXCEDIO DEL TIEMPO PREVISTO PARA CONSULTAR DATOS EN SIGUELO'
    historial.error(mensaje)
    return "TIMEEXCEDIDO"
def solucion_captcha(page:Page,historial:Logger,registro):
    cantidad_errores=0
    while cantidad_errores<5:
        captcha=resolverCaptcha(page,historial)
        page.locator('#codigoCaptcha').fill(captcha)
        page.click("button:has-text('BUSCAR')")
        page.is_enabled("#swal2-content")
        ingresoASiguelo = estadoIngresoSiguelo(page,historial)
        if ingresoASiguelo=="EXITOSO":
            return True
        elif ingresoASiguelo=="TIMEEXCEDIDO":
            #SE EXCEDIO DEL TIEMPO PREVISTO PARA CONSULTAR DATOS EN SIGUELO
            registro["observacion"] ="Error al intentar ingresar a Siguelo. (Revisar página de SUNARP)"
            return False
        else:
            if 'CAPTCHA' in ingresoASiguelo:
                page.keyboard.press("Escape")
                page.keyboard.press("Escape")
                cantidad_errores+=1
                mensaje=f"tenemos {cantidad_errores} intentos erroneos"
                historial.obs(mensaje)
                time.sleep(0.5)
                continue
            else:
                mensaje=ingresoASiguelo.replace('\n','').replace('  ','')
                historial.obs(mensaje)
                return False