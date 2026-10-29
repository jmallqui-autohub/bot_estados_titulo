import os
import time
import traceback
import json
from utils.logger import Logger
from camoufox.sync_api import Camoufox
from playwright.sync_api import Page
from resources.datosfijos import *
from utils.funciones import obtener_pdf_carga,actualizar_bitacora,concatenar_pdf,transformar_b64
from resources.inmatriculacion import Inmatriculacion
from middleware.apis import enviar_datos_opencloud,enviar_seguimiento
from middleware.funciones_correo import enviar_correo
from datetime import datetime
def login_opcloud(page,historial:Logger, url_base):
    try:
        user=os.getenv('USER_OPCLOUD')
        pws=os.getenv('PASSWORD_OPCLOUD')
        page.goto(f'{url_base}com.system.login',wait_until='load')
        time.sleep(4)
        if page.query_selector('#vUSERNAME'):
            page.locator("#vUSERNAME").click()
            page.keyboard.type(user)
            time.sleep(1)
            page.locator("#vUSERPASSWORD").click()
            page.keyboard.type(pws)
            time.sleep(1)
            with page.expect_navigation():
                page.locator('#BTNENTER').click()
            mensaje='Se inicio sesion el en OPCLOUD'
            historial.info(mensaje)
            time.sleep(5)
            return True
        else:
            mensaje='La sesion ya esta iniciada'
            historial.info(mensaje) 
            return True
    except Exception as e:
        mensaje=f'Error al Iniciar sesion en el OPCLOUD. {e}'
        historial.error(mensaje)
def guardando_datos(page,historial:Logger,registro):
    try:
        historial.obs('guardando los datos')
        tiempo_espera=0
        hora_inicio=time.time()
        mensaje_resultado=''
        page.locator('#BTNBTNGUARDAR').click()
        while(tiempo_espera<25):
            mensaje_resultado=page.evaluate('document.querySelector("body > div:nth-child(45) > div")')
            if mensaje_resultado:
                mensaje_resultado=page.evaluate('document.querySelector("body > div:nth-child(45) > div").innerText')
                break
            else:
                tiempo_espera=time.time() - hora_inicio
                time.sleep(1)
        if mensaje_resultado:
            if str(mensaje_resultado).find('Satisfactorio') != -1:
                historial.info(f'Se registro Correctamente el kardex: {registro['kardex']}')
                return True
        else:return False
    except Exception as e:
        historial.error(f'Error al guardar los datos en el sistema. {e}')
        return False   

def llenar_datos(page,historial:Logger,registro1):
    try:  
        #Se llenan los datos fijos: kardex, titulo, tramite, oficina,estadotitulo
        registros_procesar=[]
        cont=0
        #print(f'La firme {registro1}')
        #Se llenan los datos de pendiendo los estados
        if registro1['estadosiguelo'] in ['OBSERVADO','SUSPENDIDO']:
            registro1['montoDevolver']=0
            registro1['estadosiguelo']='OBSERVADO'
            registros_procesar.append(registro1)
        elif registro1['estadosiguelo'] =='TACHADO':
            registro2={}
            registro2['estadosiguelo']='POR DEVOLVER'
            registro2['fvencimiento']=registro1['fvencimiento']
            montoxdevolver=registro1['montoDevolver']
            registro2['montoDevolver']=montoxdevolver
            registro2['kardex']=registro1['kardex']
            registro2['titulo']=registro1['titulo']
            registro2['tramite']=registro1['tramite']
            registro2['oficina']=registro1['oficina']
            registros_procesar.append(registro1)
            registros_procesar.append(registro2)
            print(f'el registro: {registro1}')
            print(f'el registro con monto: {registro2}')
        elif registro1['estadosiguelo']=='LIQUIDADO':
            registros_procesar.append(registro1)
        elif registro1['estadosiguelo'] == 'REINGRESADO':
            registros_procesar.append(registro1)
        else:registros_procesar.append(registro1)
        for registro_procesar in registros_procesar:
            cont+=1
            kardex=registro_procesar['kardex']
            titulo=registro_procesar['titulo']
            tramite=registro_procesar['tramite']
            cod_tramite=tipo_tramite[tramite]
            cod_estadotitulo=tipo_estado_titulo[registro_procesar['estadosiguelo']]
            montoxdevolver=registro_procesar['montoDevolver']
            fecha_vencimiento=registro_procesar['fvencimiento']
            oficina=registro_procesar['oficina']
            if oficina =='CAÃ‘ETE': oficina='CAÑETE'
            elif oficina =='ISLAY-MOLLENDO' or oficina  == 'ISLAY':oficina='ISLAY'
            elif oficina == 'LA MERCED (SELVA CENTRAL)':oficina='LA MERCED'
            time.sleep(2)
            page.locator(f'#vKARCOD_000{cont}').fill(kardex)
            time.sleep(1)
            page.locator(f'#vKRPUBTREG_000{cont}').fill(titulo)
            time.sleep(1)
            page.locator(f'#vKRPUBTTRA_000{cont}').select_option(cod_tramite)
            time.sleep(1)
            page.locator(f'#vKRPUBINDREG_000{cont}').select_option(cod_estadotitulo)
            time.sleep(1)
            if montoxdevolver and registro_procesar['estadosiguelo'] != 'TACHADO':page.locator(f'#vMONTO_000{cont}').fill(str(montoxdevolver))
            time.sleep(1)
            if fecha_vencimiento and registro_procesar['estadosiguelo'] in ['LIQUIDADO','OBSERVADO']:page.locator(f'#vKRPUBFCHVEN_000{cont}').fill(fecha_vencimiento)
            time.sleep(1)
            page.locator(f'#vOFICOD_000{cont}').select_option(label=oficina)
            time.sleep(1)
            if registro_procesar['estadosiguelo'] not in ['POR DEVOLVER','REINGRESADO']:
                ruta_concatenado=obtener_pdf_carga(historial,registro_procesar)
                if not ruta_concatenado:return False
                page.locator(f'#vIMGARCHIVOS_000{cont}').click()
                iframe=page.frame_locator('#gxp0_ifrm')
                historial.debug('Se encontro el frame')
                time.sleep(1)
                with page.expect_file_chooser() as info:
                    iframe.locator('#FILEUPLOADContainer > div > div.row.fileupload-buttonbar > div.col-lg-7 > span.btn.btn-success.fileinput-button').click()
                seleccionar=info.value
                seleccionar.set_files(ruta_concatenado)
                nombre_doc_cargado=iframe.locator('#FILEUPLOADContainer > div > table > tbody > tr > td:nth-child(2) > p > span').inner_text(timeout=10000)
                if not nombre_doc_cargado:
                    historial.error('No figura el archivo cargado')
                    return False
                else:
                    iframe.locator('#BTNBTNADJUNTAR').click()
                    historial.info(f'Archivo cargado: {nombre_doc_cargado}')
            time.sleep(2)
        historial.info('Se ingresaron todos los datos')
        time.sleep(5)
        return True
        #page.evaluate("""document.querySelector('body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(4) > td > a > span').click()""")
    except Exception as e:
        mensaje=f'Error al ingresar los datos. {e}'
        traceback.print_exc()
        historial.error(mensaje)
        return False
def carga_opcloud(page,historial:Logger,url_base, registro):
    try:
        page.goto(f'{url_base}com.system.wpbanrrpp',wait_until='load')
        time.sleep(2)
        page.locator('#vTIPOKARDEX').select_option('I')
        time.sleep(2)
        if not llenar_datos(page,historial,registro) : return False
        time.sleep(2)
        return True
    except Exception as e:
        mensaje=f'Error en cargar los datos en el OPCLOUD. {e}'
        historial.error(mensaje)
        return False
def proceso_opcloud(registro,historial:Logger,page):
    try:
        # with Camoufox(headless=True) as browser:
        #     context = browser.new_context(ignore_https_errors=True)
        #     page = context.new_page()
            url_base=os.getenv('URL_OPCLOUD')
            registro_base=registro
            if not login_opcloud(page,historial,url_base):
                registro['observacion']=f'Fallo en el login al opencloud'
                registro['estado']='OPENCLOUD' 
                return registro
            if not carga_opcloud(page,historial,url_base,registro):
                registro_base['observacion']=f'Fallo en la carga de la inmatriculacion al opencloud'
                registro_base['estado']='OPENCLOUD' 
                return registro_base
            if not guardando_datos(page,historial,registro):
                registro_base['observacion']=f'Fallo al guardar al opencloud'
                registro_base['estado']='OPENCLOUD' 
                return registro_base 
            if registro_base['estadosiguelo'] in ['SUSPENDIDO','OBSERVADO']:
                registro_base['estasiguelo']='OBSERVADO'
                registro_base['estado']='OBSERVADO'
                ruta_esquela=obtener_pdf_carga(historial,registro_base)
                nombre_esquela=os.path.basename(ruta_esquela)
                os.remove(ruta_esquela)
                historial.info(f'Se elimino la esquela de observacion: {nombre_esquela}')
            elif registro_base['estadosiguelo']=='LIQUIDADO': registro_base['estado']='LIQUIDADO'
            elif registro_base['estadosiguelo']=='INSCRITO': registro_base['estado']='LISTO'
            elif registro_base['estadosiguelo']=='TACHADO': registro_base['estado']='LISTO'
            elif registro_base['estadosiguelo']=='REINGRESADO': registro_base['estado']='REINGRESADO'
            return registro_base
    except Exception as e:
        actualizar_bitacora(registro_base)
        mensaje=f'Fallo en el proceso del OPCLOUD. {e}'
        historial.error(mensaje)
        registro['observacion']=mensaje
        registro['estado']='OPENCLOUD'
        return registro

def actualizar_opencloud(historial:Logger,registro:Inmatriculacion):
    try:
        historial.title('Enviando los datos a la plataforma del opencloud')
        ruta_archivo=''
        base64=''
        ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{registro.titulo}-{registro.anio}')
        ruta_json=os.path.join(ruta_carpeta,f'payload_{registro.kardex}.json')
        estado_opencloud=tipo_estado_titulo[registro.estado_siguelo]
        oficina_opencloud=OFICINAS[registro.oficina]
        fecha_opencloud=datetime.strptime(registro.fecha_estado, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        monto=float(registro.monto_devolver) if registro.monto_devolver else 0
        match registro.estado_siguelo:
            case 'INSCRITO':
                ruta_archivo=concatenar_pdf(historial, registro)
                base64=transformar_b64(ruta_archivo)
            case 'OBSERVADO':
                ruta_archivo=os.path.join(ruta_carpeta,'ESQUELA_OBSERVACION.pdf')
                base64=transformar_b64(ruta_archivo)
            case 'LIQUIDADO':
                ruta_archivo=os.path.join(ruta_carpeta,'ESQUELA_LIQUIDACION.pdf')
                base64=transformar_b64(ruta_archivo)
            case 'TACHADO':
                ruta_archivo=os.path.join(ruta_carpeta,'ESQUELA_TACHA.pdf')
                base64=transformar_b64(ruta_archivo)
            case _:
                historial.obs('Caso sin archivo')
        body={
                "TipoLiquida":"I",
                "Kardex":registro.kardex,
                "Titulo":registro.titulo,
                "Tramite":"A",
                "Estado":estado_opencloud,
                "FechaEstado":fecha_opencloud,
                "FechaVenc":registro.fecha_vencimiento,
                "Monto":monto,
                "Oficina":oficina_opencloud,
                "Adjunto":base64
            }
        with open(ruta_json, "w", encoding="utf-8") as archivo:
            json.dump(body, archivo, indent=4, ensure_ascii=False)
        resp=enviar_datos_opencloud(historial,body)
        if resp:
            registro.observacion=f'Estado del Siguelo: {registro.estado_siguelo}'
            if not registro.orden_giro:enviar_seguimiento(historial,registro,'open-cloud-ogiro',registro.observacion)
            else:enviar_seguimiento(historial,registro,'open-cloud',registro.observacion)
        # else:
        #     subject=f"Error Carga de estados titulos OpenCloud - Nro Inmatriculacion {registro.interno} "
        #     mensaje=f"titulo:{registro.titulo} - Kardex: {registro.kardex} - Estado: {registro.estado_siguelo}" 
        #     enviar_correo(CORREOS_ERROR,subject,mensaje,1,'','',False,historial)

    except Exception as e:
        historial.error(f'Error en el envio de los datos al opencloud.{e}')
