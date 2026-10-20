# import easyocr
import base64
import os
import shutil
import json
import re
import fitz
# import easyocr
import random
import time as dt
import threading
import pandas as pd
import socket
import requests
import urllib.request
from pdf2image import convert_from_path
import pdfplumber
from utils.logger import Logger
from resources.datosfijos import *
from pypdf import PdfReader
from datetime import datetime,timedelta,time
from PyPDF2 import PdfMerger
from camoufox.sync_api import Camoufox
from PIL import Image
from datetime import datetime
from middleware.apis import *


def input_con_timeout(prompt, timeout=5, default=0):
    """Obtiene entrada del usuario con timeout. Si no se ingresa nada, devuelve el valor por defecto."""
    print(prompt, end='', flush=True)
    resultado = [None]

    def obtener_input():
        try:
            resultado[0] = input()
        except:
            pass  # En caso de error, se mantiene como None

    hilo = threading.Thread(target=obtener_input)
    hilo.daemon = True  # Para que no bloquee la salida del programa
    hilo.start()
    hilo.join(timeout)

    if hilo.is_alive():
        print(f"\nTiempo agotado. Se usará el valor por defecto: {default}")
        return default
    else:
        return resultado[0] if resultado[0] != '' else default
def obtener_fila_inicio(registros):
    fila_inicio=None
    if registros:
        ultimo_registro=registros[-1]
        ultima_fila=ultimo_registro['fila']
        ultima_fila=int(ultima_fila)
        # Usamos la función con timeout
        entrada = input_con_timeout("(Opcional) Inserte la fila de inicio (tiene 5 segundos): ", timeout=5, default=0)
        
        if entrada != 0:  # Si el usuario escribió algo
            try:
                fila_inicio = int(entrada)
                if fila_inicio > ultima_fila:
                    print('Fila inválida')
                    return obtener_fila_inicio(registros)  # Recursión
                else:
                    print(f'Válido, fila {fila_inicio}')
                    return fila_inicio
            except ValueError:
                print('Entrada no válida. Intente de nuevo.')
                return obtener_fila_inicio(registros)
        else:
            print('Se usará la fila 0 por defecto.')
            return 0
        # fila_inicio=input("(Opcional) Inserte la fila de inicio: ")
        # if fila_inicio:
        #     fila_inicio=int(fila_inicio)
        #     if fila_inicio>ultima_fila:
        #         print('fila invalida')
        #         return obtener_fila_inicio(registros)
        #     else:
        #         print(f'valido fila {fila_inicio}')
        #         return fila_inicio
        # else:
        #     return 0
    else : return 0
def filtrar_filas(registros,fila_inicio,historial:Logger):
    registros_procesar=[]
    if fila_inicio:
        for registro in registros:
            fila=int(registro['fila'])
            if fila<fila_inicio:
                mensaje=f'Omitiendo fila {registro['fila']}'
                historial.debug(mensaje)
            else:registros_procesar.append(registro)
        return registros_procesar
    else:return registros
def transformar_b64(rutaFile):

    with open(rutaFile, 'rb') as archivo:
                    # Lee el contenido del archivo
        contenido_pdf = archivo.read()
                    # Codifica el contenido en Base64
        pdf_base64 = base64.b64encode(contenido_pdf).decode('utf-8')
        
    return pdf_base64
def verificar_hora_ejecucion():
    hora_actual=datetime.now().time()
    hora_minima=time(8,0)
    hora_maxima=time(23,59)
    if hora_maxima<=hora_actual:return False
    elif hora_actual<=hora_minima:return False
    else:return True
def obtener_carpeta_descarga(kardex,titulo):
    ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{kardex}-{titulo}')
    if os.path.exists(ruta_carpeta):return ruta_carpeta
    else:
        os.mkdir(ruta_carpeta)
        return ruta_carpeta

def pdf_legible(ruta):
    try:
        documento = fitz.open(ruta)
        texto_total = ""

        for pagina_num in range(len(documento)):
            pagina = documento.load_page(pagina_num)
            texto_pagina = pagina.get_text("text")
            texto_total += texto_pagina

        documento.close()

        # Si hay suficiente texto, se considera legible
        if len(texto_total.strip()) > 20:
            return True
        else:
            return False
    except:return False
def procesar_texto(texto,tipo,subtipo):
    if tipo == 'OBSERVADO':
        if subtipo==1:expresion_regular=r"\d{2}/\d{2}/\d{4}\s*-\s*Subsanar hasta el\s*:\s*\d{2}/\d{2}/\d{4}"
        else:expresion_regular=r'\d{2}/\d{2}/\d{4}'
    elif tipo=='TACHADO':
        expresion_regular=r'SI\.?\s+(\d+\.?\d*)'
    else: expresion_regular=''
    busqueda=re.search(expresion_regular,texto,re.IGNORECASE)
    if busqueda and tipo == 'OBSERVADO':
        fecha_vencimiento=busqueda.group(0)
        fecha_vencimiento=fecha_vencimiento.split('-')[0]
        fecha_vencimiento=fecha_vencimiento.strip()
        fecha = datetime.strptime(fecha_vencimiento, "%d/%m/%Y")
        fecha_menos_7 = fecha - timedelta(days=7)
        fecha_vencimiento = fecha_menos_7.strftime("%d/%m/%Y")
        return fecha_vencimiento
    elif busqueda and tipo=='TACHADO':
        montoxDevolver=busqueda.group(0)
        montoxDevolver=montoxDevolver.replace('SI','').replace('SI.','').strip()
        return montoxDevolver
    else:return False

def obtener_fecha_vencimiento(seccion):
    todas_las_fechas = re.findall(r"(\d{2}/\d{2}/\d{4})", seccion)
    
    if not todas_las_fechas:
        return False

    if len(todas_las_fechas) >= 2:
        return todas_las_fechas[-1]

    if len(todas_las_fechas) == 1:
        patron_especifico = r"Fecha\s+Vencimiento[\s\S]{0,50}(\d{2}/\d{2}/\d{4})"
        busqueda = re.search(patron_especifico, seccion, re.IGNORECASE)
        if busqueda:
            return busqueda.group(1).strip()
            
    return todas_las_fechas[0]

def procesar_texto_api(texto,tipo,subtipo, historial):
    if tipo == 'OBSERVADO':
        inicio_tag = "Oficina Registral"
        fin_tag = "Señor(es)"
        
        idx_inicio = texto.find(inicio_tag)
        idx_fin = texto.find(fin_tag)
        
        seccion = texto[idx_inicio:idx_fin] if idx_inicio != -1 and idx_fin != -1 else texto

        historial.debug(f'Sección extraída para OBSERVADO: {seccion}')

        resultado_fecha = obtener_fecha_vencimiento(seccion)
    
        historial.debug(f'Fecha de vencimiento extraída para OBSERVADO: {resultado_fecha}')
    
        if resultado_fecha:
            try:
                fecha_dt = datetime.strptime(resultado_fecha, "%d/%m/%Y")
                return fecha_dt.strftime("%d/%m/%Y")
            except ValueError:
                return False
        
        return False

    elif tipo == 'TACHADO':
        expresion_regular = r'(?:SI\.?|S/)\s*(\d+\.?\d*)'
        busqueda = re.search(expresion_regular, texto, re.IGNORECASE)
        
        if busqueda:
            return busqueda.group(1).strip()
        return False
        
    return False

def obtener_datos_pdf_api(historial:Logger,ruta, titulo):
    try:
        pdf_base64=transformar_b64(ruta)
        texto_obtenido=leer_documentos_api(historial,pdf_base64)
        if texto_obtenido:
            fecha_vencimiento=procesar_texto_api(texto_obtenido,'OBSERVADO',1, historial)
            return fecha_vencimiento
        else: return False
    except Exception as e:
        historial.error(f'Fallo al obtener el dato del pdf a través del API. {e}')
        return False

def obtener_pdf_carga(historial:Logger,registro):

    # obtenemos el tipo de caso a subir:
    estado_titulo=registro['estadosiguelo']
    titulo=registro['titulo']
    anio=registro['anio']
    ruta_base=os.path.join(RUTAPRIN,'download',f'{titulo}-{anio}')
    match estado_titulo:
        case 'INSCRITO':
            nombre_inscripcion=''
            nombre_anotacion=''
            nombre_orden_giro=''
            nombre_tive=''
            pdfs_concatenar=[]
            for nombre_archivo in os.listdir(ruta_base):
                if 'TIVE' in nombre_archivo and not nombre_tive:
                    nombre_tive=nombre_archivo
                if 'GIRO' in nombre_archivo and not nombre_orden_giro:
                    nombre_orden_giro=nombre_archivo
                if 'NOTA' in nombre_archivo:
                    nombre_anotacion=nombre_archivo
                if 'nota' in nombre_archivo:
                    nombre_anotacion=nombre_archivo
                if 'asiento' in nombre_archivo :
                    nombre_inscripcion=nombre_archivo
                if 'ASIENTO' in nombre_archivo:
                    nombre_inscripcion=nombre_archivo
                if f'{titulo}.pdf' == nombre_archivo:
                    nombre_inscripcion=nombre_archivo
            
            ruta_tive=os.path.join(ruta_base,nombre_tive)
            ruta_insc=os.path.join(ruta_base,nombre_inscripcion)
            ruta_anotacion=os.path.join(ruta_base,nombre_anotacion)
            ruta_og=os.path.join(ruta_base,nombre_orden_giro)
            pdfs_concatenar.append(ruta_tive)
            pdfs_concatenar.append(ruta_insc)
            pdfs_concatenar.append(ruta_anotacion)
            pdfs_concatenar.append(ruta_og)
            pdfs_concatenar.sort()
            ruta_pdf_concatenado=os.path.join(ruta_base,f'concatenado_{titulo}-{anio}.pdf')
            fusionPdf=PdfMerger()
            for pdf in pdfs_concatenar:
                with open(pdf,'rb') as file:
                    fusionPdf.append(file)
            with open(ruta_pdf_concatenado,'wb') as salida:
                fusionPdf.write(salida)
            historial.info(ruta_pdf_concatenado)
            return ruta_pdf_concatenado
        case 'OBSERVADO':
            fecha=registro['fvencimiento']
            fecha=fecha.replace('/','-')
            ruta_esquela=os.path.join(ruta_base,f'ESQUELA_OBSERVACION_{titulo}_{fecha}.pdf')
            historial.debug(ruta_esquela)
            return ruta_esquela
        case 'LIQUIDADO':return None
        case 'TACHADO':
            ruta_esquela=os.path.join(ruta_base,f'ESQUELA_TACHA_{titulo}.pdf')

def obtener_pdf_link(historial: Logger, registro: dict, link, ruta, page=None):
    if page is not None and not page.is_closed():
        page.goto(link, wait_until='load')
        page.evaluate("""document.querySelector('#frmEsquela>span>div').remove()""")
        page.pdf(path=ruta, format='A4', print_background=True)
        nombre_ruta = os.path.basename(ruta)
        dt.sleep(5)
        historial.info(f'Se descargo el pdf {nombre_ruta}')
    else:
        with Camoufox(headless=True) as browser:
            context = browser.new_context(ignore_https_errors=True)
            p = context.new_page()
            p.goto(link, wait_until='load')
            p.evaluate("""document.querySelector('#frmEsquela>span>div').remove()""")
            p.pdf(path=ruta, format='A4', print_background=True)
            nombre_ruta = os.path.basename(ruta)
            dt.sleep(5)
            p.close()
            historial.info(f'Se descargo el pdf {nombre_ruta}')

def convertir_png_pdf(rutaorigen,rutadestino):
    imagen=Image.open(rutaorigen)
    if imagen.mode in ('RGBA','LA','P'):
        imagen=imagen.convert('RGB')
    imagen.save(rutadestino,'PDF',resolution=100.0)


def obtener_datos_inscripcion(historial:Logger,ruta):
    historial.obs('iniciando con la obtencion de los datos de la inscripcion')
    texto_obtenido=''
    placa=''
    nro_partida=''
    nro_titulo=''
    with pdfplumber.open(ruta) as pdf:
        for i, pagina in enumerate(pdf.pages):
            texto=pagina.extract_text()
            texto_obtenido=texto_obtenido+' '+texto
    #print(texto_obtenido)
    expresion_placa=r"Placa\s*:\s*([^\n]+)"
    expresion_partida=r'Partida\s+Nro\s*:\s*([^\n]+)'
    expresion_titulo=r'Título\s+Nro\s*:\s*([^\n]+)'
    consulta=re.search(expresion_placa,texto_obtenido,re.IGNORECASE)
    consulta2=re.search(expresion_partida,texto_obtenido,re.IGNORECASE)
    consulta3=re.search(expresion_titulo,texto_obtenido,re.IGNORECASE)
    if consulta: placa=consulta.group(0)
    if consulta2: nro_partida=consulta2.group(0)
    if consulta3: nro_titulo=consulta3.group(0)
    if placa:placa=placa.split(':')[1].strip()
    if nro_partida:
        nro_partida=nro_partida.split(':')[1].strip()
    else:
        expresion_partida=r'Partida\s*([^\n]+)'
        consulta4=re.search(expresion_partida,texto_obtenido,re.IGNORECASE)
        if consulta4:
            nro_partida=consulta4.group(0)
            nro_partida=nro_partida.replace('Partida','').strip()

    if nro_titulo:
        nro_titulo=nro_titulo.split(':')[1].strip()
    else:
        expresion_titulo=r'Título\s+Nro\s*([^\n]+)'
        consulta5=re.search(expresion_titulo,texto_obtenido,re.IGNORECASE)
        if consulta5:
            nro_titulo=consulta5.group(0)
            nro_titulo=nro_titulo.split('-')[1].strip()
    historial.debug(nro_partida)
    historial.debug(nro_titulo)
    historial.debug(placa)
    return placa,nro_partida,nro_titulo

def mover_archivos(ruta_origen,ruta_destino,tipo):
    cont=0
    while cont<60:
        archivos = [f for f in os.listdir(ruta_origen) if os.path.isfile(os.path.join(ruta_origen, f))]
        dt.sleep(1)
        if archivos:break
        cont+=1
    if archivos:
        print("Hay archivos en el directorio.")
        for archivo in os.listdir(ruta_origen):
            ruta_archivo=os.path.join(ruta_origen,archivo)
            ruta_destino_archivo=os.path.join(ruta_destino,f'{tipo}.pdf')
            shutil.copy2(ruta_archivo,ruta_destino_archivo)
            os.remove(ruta_archivo)
            print('Se copio el archivo')
        return True
    else:
        print("No hay archivos en el directorio.")
        return False

def human_pause(min_ms=500, max_ms=1000):
    # Generar delay aleatorio
    delay = random.uniform(min_ms, max_ms) / 1000.0

    # Registrar hora inicial
    # start_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    # print(f"🕒 Inicio pausa: {start_time}")

    # Mostrar delay
    #print(f"⏳ Delay generado: {delay:.3f} segundos")

    # Pausa real
    dt.sleep(delay)

    # Registrar hora final
    # end_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    # print(f"✅ Fin pausa: {end_time}\n")

def calcular_dias_habiles(fecha):
    fecha_inicio=datetime.strptime(fecha,'%d/%m/%Y')
    fecha_inicio=fecha_inicio.date().strftime("%Y-%m-%d")
    fecha_actual=datetime.now().date().strftime("%Y-%m-%d")
    inicio = pd.to_datetime(fecha_inicio)
    fin = pd.to_datetime(fecha_actual)
    # Generar rango de fechas hábiles (lun-vie)
    rango = pd.bdate_range(start=inicio, end=fin, holidays=LISTA_FERIADOS,freq="C")
    dias_habiles = max(0,len(rango)-1)
    print(f"Días hábiles: {dias_habiles}")
    if dias_habiles>7: return True,dias_habiles
    else:return False,dias_habiles


def dias_habiles(fecha):
    try:
        if not fecha:return False
        fecha_consulta=datetime.strptime(fecha,"%d/%m/%Y")
        fecha_actual=datetime.now().date()
        dias_contados=0
        while dias_contados<1:
            fecha_actual-=timedelta(days=1)
            if fecha_actual.weekday()<5:
                dias_contados +=1
        if fecha_consulta.date() <= fecha_actual: return True
        else:return False 
    except:return False 

def cambiar_formato_fecha(fecha:str):
    try:
        fecha_date=datetime.strptime(fecha,"%Y-%m-%d")
        return fecha_date.strftime("%d/%m/%Y")
    except Exception as e:
        print(f'Error al cambiar el formato de la fecha: {e}')
        return ''
def actualizar_bitacora(registro:dict):
    with open(RUTA_BITACORA,'r',encoding='utf-8') as file:
        datos=json.load(file)
    if str(registro['inmatriculacion']) in datos:
        datos[str(registro['inmatriculacion'])]={'intentos':2}
    else:
        datos[str(registro['inmatriculacion'])]={'intentos':1}
    with open(RUTA_BITACORA,'w',encoding='utf-8') as file:
        json.dump(datos,file,indent=4,ensure_ascii=False)

def obtener_contador_intentos(inmatriculacion):
    with open(RUTA_BITACORA,'r',encoding='utf-8') as file:
        datos=json.load(file)
    contador=datos[str(inmatriculacion)]['intentos']
    return contador
def obtener_data_bitacora():
    with open(RUTA_BITACORA,'r',encoding='utf-8') as file:
        datos=json.load(file)
    return datos
def limpiar_json(historial:Logger):
    try:
        with open(RUTA_BITACORA, 'w', encoding='utf-8') as archivo:
            json.dump({}, archivo)
        historial.debug('Se limpio la bitacora')
    except Exception as e:
       historial.error(f"Error al limpiar el archivo: {e}")

def obtener_ip_red(historial:Logger):
    try:
        externa=urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        ip_local=externa
    except Exception as e:
        historial.error(f'error al capturar la ip {e}')
        ip_local='127.0.0.1'
    return ip_local

def verificar_hora_pausa(hora_inicio:datetime):
    try:
        hora_actual=datetime.now()
        resta=hora_actual-hora_inicio
        minutos_pasados=resta.total_seconds()/60
        if minutos_pasados>=20:return False
        else:return True
    except Exception as e:
        return False
def pausar_bot(historial:Logger):
    tiempo_espera=0
    valor=False
    tiempo_limite=int(os.getenv('TIEMPO_ESPERA'))
    historial.debug(f'El tiempo de espera es: {tiempo_limite}')
    while tiempo_espera<tiempo_limite:
        respuesta=respuesta_usuario(historial)
        dt.sleep(10)
        tiempo_espera+=1
        if respuesta:
            valor=True 
            break
    return valor

def notificar_bot(historial:Logger,registro:Inmatriculacion):
    try:
        dt.sleep(60)
        respuesta=notificar_baneo(historial)
        if respuesta:
            historial.info(f'Se informo al sistema sobre el baneo')
            enviar_seguimiento(historial,registro,'siguelo-baneado')
            dt.sleep(300)
            if encender_modem(historial):
                dt.sleep(60)
                if not habilitar_bot(historial):
                    enviar_webhoook(f'ERROR - BOT {os.getenv('BOT_ASIGNADO')}','URGENTE',f'No se pudo habilitar los bots despues del baneo - modem {os.getenv('MODEM')}')
            else:
                enviar_webhoook(f'ERROR - BOT {os.getenv('BOT_ASIGNADO')}','URGENTE',f'No se pudo encender el modem {os.getenv('MODEM')}')
    except Exception as e:
        historial.error(f'Error en el proceso de notificar al sistema el baneo. {e}')

def verificar_conexion(historial:Logger):
        verificar_hora=True
        while True:
            if not verificar_hora_ejecucion(): 
                verificar_hora=False
                break
            if probar_conexion(historial):
                historial.info('Hay conexion a internet')
                break
            historial.debug("esperando conexion")
            dt.sleep(30)
        return verificar_hora

def concatenar_pdf(historial:Logger,registro:Inmatriculacion):

    # obtenemos el tipo de caso a subir:
    ruta_base=os.path.join(RUTAPRIN,'download',f'{registro.titulo}-{registro.anio}')
    ruta_pdf_concatenado=os.path.join(ruta_base,f'concatenado_{registro.titulo}-{registro.anio}.pdf')
    if os.path.exists(ruta_pdf_concatenado):os.remove(ruta_pdf_concatenado)
    pdfs_concatenar=[]
    for nombre_archivo in os.listdir(ruta_base):
        if nombre_archivo.lower().endswith('.pdf'):
            ruta_archivo=os.path.join(ruta_base,nombre_archivo)
            pdfs_concatenar.append(ruta_archivo)
    pdfs_concatenar.sort()
    fusionPdf=PdfMerger()
    for pdf in pdfs_concatenar:
        with open(pdf,'rb') as file:
            fusionPdf.append(file)
    with open(ruta_pdf_concatenado,'wb') as salida:
        fusionPdf.write(salida)
    historial.debug(f'ruta del concatenado:{ruta_pdf_concatenado}')
    return ruta_pdf_concatenado

def obtener_datos_inscripcionV2(historial:Logger,ruta):
    placa=''
    try:
        pdf_base64=transformar_b64(ruta)
        texto=leer_documentos_api(historial,pdf_base64)
        if texto:
            texto=texto.replace('\n',' ')
            expresion_regular=r'Placa\s*:?\s*([A-Za-z0-9]{6})'
            consulta=re.search(expresion_regular,texto,re.IGNORECASE)
            if consulta:
                valor=consulta.group(0)
                placa=valor.split(':')[-1].strip()
        return placa
    except Exception as e:
        historial.error(f'Fallo en la obtencion del dato de la placa atraves del AWs:{e} ')
        return placa
