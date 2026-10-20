import os 
import requests
import ssl
import urllib3
from requests.adapters import HTTPAdapter
from utils.logger import Logger
from resources.inmatriculacion import Inmatriculacion
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def enviar_datos_inscripcion(body,historial:Logger):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/bots/titulos/inscrito'
        response=requests.post(url,json=body)
        if response.status_code == 200:
            return response.status_code
        else: return response.status_code
    except Exception as e:
        mensaje=f'Error al enviar por api los datos de la inscripcion. {e}'
        historial.error(mensaje)
        return None
def enviar_documentos_estado(historial:Logger,body:dict,registro:Inmatriculacion):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/tramite/titulo'
        response=requests.post(url,json=body)
        if response.status_code == 201:
            historial.info('Se envio los documentos y se actualizo el sistema correctamente')
            return True
        else: 
            historial.obs(f'Ocurrio un fallo en el envio de los documentos y estados al sistema. {response.json()}')
            enviar_seguimiento(historial,registro,'error-general',f'{response.json()}')
            return False
    except Exception as e:
        historial.error(f'Error al enviar por api los datos de la inscripcion. {e}')
        return False

def obtener_asesores_asociados(body,historial:Logger):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/bots/titulos/observado'
        reponse =requests.post(url,json=body)
        if reponse.status_code == 200:
            return reponse.json()
        else:
            mensaje=f"Error al obtener los abogados asociados: {reponse.status_code}"
            historial.obs(mensaje)
            return None
    except Exception as e:
        mensaje=f"Error al consultar la api: {e}"
        historial.error(mensaje)
        return None
def descargar_archivo_link(historial:Logger,registro:dict,link,ruta):
    try:
        class PermissiveSSLAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.set_ciphers('DEFAULT@SECLEVEL=1')
                kwargs['ssl_context'] = context
                return super().init_poolmanager(*args, **kwargs)

        session = requests.Session()
        session.mount('https://', PermissiveSSLAdapter())

        headers = {
            'Accept': '/',
            'User-Agent': 'Thunder Client (https://www.thunderclient.com)'
        }

        response = session.get(link, headers=headers, timeout=600, verify=False)
        response.raise_for_status()
        with open(ruta, 'wb') as f:
            f.write(response.content)
        return True

    except Exception as e:
        historial.error(f'Error al descargar el archivo {e}')
        return False

    finally:
        if 'session' in locals():
            session.close()

def reclamos(historial:Logger,registro:dict):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/tramite/reclamo'
        body={"tramite":registro['inmatriculacion']}
        response=requests.post(url,json=body)
        if response.status_code == 200:
            return response.json()
        else:
            historial.obs(f'respuesta : {response.status_code},  {response.json()}')
            return False
    except Exception as e:
        mensaje=f'Error al enviar por api los datos de la inscripcion. {e}'
        historial.error(mensaje)
        return False

def obtener_lista_procesar(historial:Logger):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/tramite/titulos/pendientes/{os.getenv('COMPANIA')}/{os.getenv('ORDEN')}'
        response=requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            historial.obs(f'respuesta : {response.status_code},  {response.json()}')
            return ''
    except Exception as e:
        mensaje=f'Error al obtener la lista de procesar de la API: {repr(e)}'
        historial.error(mensaje)
        return ''

def enviar_estado_siguelo(historial:Logger,estado_siguelo,registro:Inmatriculacion):
    try:
        body={"tramite":registro.interno,"titulo":registro.titulo,"estado":estado_siguelo}
        url=f'{os.getenv('URL_API_PROD')}/servicios/tramite/titulos/estado'
        response=requests.post(url,json=body)
        if response.status_code == 200:
            historial.info(f'Se envio el estado siguelo {estado_siguelo} del tramite {registro.interno}')
            return True
        else:
            historial.obs(f'respuesta : {response.status_code},  {response.json()}')
            return False
    except Exception as e:
        historial.error(f'Error al enviar el estado siguelo a la API: {e}')
        return False
def respuesta_usuario(historial:Logger):
    estado=False
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/bots/siguelo/modem/estado/{os.getenv('MODEM')}'
        response=requests.get(url,timeout=3)
        historial.debug(f'respuesta del api respuesta_usuario: {response.json()}')
        if response.status_code==200:
            historial.debug('Respuesta 200')
            data=response.json()
            valor=data['estado']
            historial.debug(f'Valor : {valor}')
            if valor:
                estado =True 
                return estado
        else: 
            historial.obs(f'status: {response.status_code}, {response.json()}')
            return estado
    except Exception as e:
        historial.error(f'Error en el api de respuesta {e}')
        return estado

def enviar_webhoook(titulo,tipo,cabecera,mensaje):
    try:
        #url='https://chat.googleapis.com/v1/spaces/AAQAMJ29KiM/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=bjcEtJfP7nRF-CD5DWTxpqB6Czt2uXaBFSSHGKrJjGk'
        url='https://chat.googleapis.com/v1/spaces/AAQA1D2B0x8/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=wGuWlC5SzP6hnesbPEOQhDFAf2Ah0Y_SXGZMfYOO_Qk'
        # Para notificar a todos, añade el campo 'text' con la mención <users/all>.
        # El texto que pongas aquí aparecerá en la notificación emergente.
        message = {
                "text": f"*{titulo}*",
                "cards_v2": [{
                    "card": {
                    "header": {
                        "title": f'{tipo}',
                    },
                    "sections": [{
                        "header": cabecera,
                        "widgets":[
                            {
                                "text_paragraph":{
                                    'text':mensaje

                                }
                            }
                        ]
                        }
                    ]
                }}]
        }

        response=requests.post(url,json=message)
        print(f'mensaje enviado {response.status_code}')
    except Exception as e:
        print(f'Error al enviar el mensaje: {e}')

def notificar_baneo(historial:Logger):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/bots/siguelo/modem/baneado/{os.getenv('MODEM')}'
        response=requests.get(url)
        if response.status_code==200:
            data=response.json()
            temporizador=data['temporizador']
            return temporizador
        else:
            historial.obs(f'respuesta del api_notificar_baneo: {response.status_code} - {response.json()}')
            return False
    except Exception as e:
        historial.error(f'Fallo el api notifica_baneo : {e}')
        return False

def encender_modem(historial:Logger):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/bots/siguelo/modem/encender/{os.getenv('MODEM')}'
        response=requests.get(url)
        if response.status_code==200:
            data=response.json()
            estado=data['estado']
            return estado
        else:
            historial.obs(f'respuesta del api_enceder_modem: {response.status_code} - {response.json()}')
            return False
    except Exception as e:
        historial.error(f'Fallo el api enceder_modem : {e}')
        return False

def habilitar_bot(historial:Logger):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/bots/siguelo/modem/habilitar/{os.getenv('MODEM')}'
        response=requests.get(url)
        if response.status_code==200:
            data=response.json()
            estado=data['estado']
            return estado
        else:
            historial.obs(f'respuesta del api_habilitar_bot: {response.status_code} - {response.json()}')
            return False
    except Exception as e:
        historial.error(f'Fallo el api habilitar_bot : {e}')
        return False

def probar_conexion(historial:Logger):
    try:
        url=f'{os.getenv('URL_API_PROD')}/servicios/bots/siguelo/modem/estado/{os.getenv('MODEM')}'
        response=requests.get(url,timeout=3)
        historial.debug(f"{response.json()}")
        if response.status_code==200:return True
        else: return True
    except Exception as e:
        return False

def enviar_observaciones(historial:Logger,body):
    try:
        url=f'{os.getenv('URL_API_PROD')}/v2/notificaciones-central/observacion-inmatriculacion'
        response= requests.post(url,json=body)
        if response.status_code == 200:
            data=response.json()
            if data['data']['esquela_guardada']:
                return True
            else: return False
        else:
            historial.obs(f'Fallo el envio de la info de la observacion. {response.json()}')
            return False
    except Exception as e:
        historial.error(f'Hubo un error al enviar los datos de la observacion al sistema. {e}')
        return False

def enviar_seguimiento(historial:Logger,registro:Inmatriculacion,codigo,detalle=""):
    try:
        body={"BOT-ID":registro.bot,"id":registro.id,"detalle":detalle}
        url=f'{os.getenv('URL_API_PROD')}/servicios/bot/{os.getenv('TIPO_BOT')}/{codigo}'
        response= requests.post(url,json=body)
        if response.status_code == 200:
            historial.info(f'Se informo al sistema, codigo de proceso: {codigo}')
            return True
        else:
            historial.obs(f'Fallo el envio de la info al seguimiento. {response.json()}')
            return False
    except Exception as e:
        historial.error(f'Hubo un error al enviar los datos del seguimiento al sistema, codigo {codigo}. {e}')
        return False


def obtener_casos_api(historial:Logger) -> list:
    casos_procesar=[]
    try:
        body={"BOT-ID": os.getenv('BOT_ID')}
        url=f'{os.getenv('URL_API_PROD')}/servicios/bot/{os.getenv('TIPO_BOT')}/pendiente/{os.getenv('LIMITE')}'
        response= requests.post(url,json=body)
        if response.status_code==200:
            casos_procesar=response.json()['tramites']
        else:
            historial.obs(f'Fallo en la obtencion de jobs para el bot. {response.json()}')
        return casos_procesar
    except Exception as e:
        historial.error(f'Error al obtener casos para trabajar del api: {e}')
        return casos_procesar

def obtener_datos_tramite(historial:Logger, registro:Inmatriculacion) -> list:
    data=[]
    try:
        body={"inmatriculacion":registro.interno,"titulo":registro.titulo}
        url=f'{os.getenv('URL_API_PROD')}/servicios/tramite/titulo/datos'
        response= requests.post(url, json=body)
        if response.status_code==200:
            data=response.json()
        else:
            historial.obs(f'Fallo en la obtencion de casos para el bot. {response.json()}')
        return data
    except Exception as e:
        historial.error(f'Error en la obtencion de los datos del tramite. {e}')
        return data

def enviar_datos_opencloud(historial:Logger, body:dict):
    try:
        url=f'{os.getenv('URL_API_OPENCLOUD')}/OPCloud/systemapirest/webhookrrppestado'
        response= requests.post(url, json=body)
        if response.status_code==200:
            historial.obs(f'Se envio correctamente la informacion al opencloud')
            return True
        else:
            historial.obs(f'Fallo en la obtencion de casos para el bot. {response.json()}')
        return False
    except Exception as e:
        historial.error(f'Error en la obtencion de los datos del tramite. {e}')
        return False
def leer_documentos_api(historial:Logger,pdf_base64:str):
    texto=''
    try:
        payload={'fileBase64':pdf_base64}
        url=f'{os.getenv('URL_API_PROD')}/servicios/integrations/aws/pdf/text'
        response = requests.post(url, json=payload)
        if response.status_code ==200:
            data=response.json()
            texto=data.get('texto','')
        else:
            historial.obs(f'Ocurrio un fallo al obtener los datos del api que lee pdf: {response.json()}')
        return texto
    except Exception as e:
        historial.error(f'Error en al obtener el texto del pdf por Api. {e}')
        return texto