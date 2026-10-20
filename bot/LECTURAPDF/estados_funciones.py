import os
import traceback
from utils.logger import Logger
from resources.datosfijos import *
from utils.funciones import transformar_b64,obtener_pdf_link, obtener_datos_pdf_api
from middleware.funciones_correo import *
from middleware.apis import *
from resources.inmatriculacion import Inmatriculacion
from datetime import datetime



def estado_inscrito(historial:Logger,registro:Inmatriculacion):
    # Nombres de los archivos
    nombre_asiento=f'{registro.titulo}.pdf'
    nombre_tive=f'{registro.titulo}_TIVE.pdf'
    nombre_OG=f'{registro.titulo}_ORDEN_GIRO.pdf'
    nombre_anotacion=f'{registro.titulo}_ANOTACION.pdf'

    # Rutas de los archivos a descargar
    ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{registro.titulo}-{registro.anio}')
    ruta_asiento=os.path.join(ruta_carpeta,nombre_asiento)
    ruta_tive=os.path.join(ruta_carpeta,nombre_tive)
    ruta_orden_giro = os.path.join(ruta_carpeta, nombre_OG)
    ruta_anotacion=os.path.join(ruta_carpeta,nombre_anotacion )

    # Lista de archivos adjuntos
    lista_adjuntos=[]

    # Se transforma a base64 los archivos descargados y se adicionan a los adjuntos de envio
    if os.path.exists(ruta_tive):
        b64_tive=transformar_b64(ruta_tive)
        adjunto={"tipo":"TIVE", "filename":nombre_tive,"base64":b64_tive}
        lista_adjuntos.append(adjunto)
    if os.path.exists(ruta_asiento):
        b64_asiento=transformar_b64(ruta_asiento)
        adjunto={"tipo":"INS", "filename":nombre_asiento,"base64":b64_asiento}
        lista_adjuntos.append(adjunto)
    if os.path.exists(ruta_orden_giro):
        b64_OG=transformar_b64(ruta_orden_giro)
        adjunto={"tipo":"OGIRO", "filename":nombre_OG,"base64":b64_OG}
        lista_adjuntos.append(adjunto)
    if os.path.exists(ruta_anotacion):
        b64_anotacion=transformar_b64(ruta_anotacion)
        adjunto={"tipo":"ANOT", "filename":nombre_anotacion,"base64":b64_anotacion}
        lista_adjuntos.append(adjunto)

    historial.obs(f"Enviando datos de la {'inscripcion' if registro.titulo_tipo=='P' else 'rectificacion'}")
    body={
            "inmatriculacion":registro.interno,
            "titulo":registro.titulo,
            "tipo":"IN",
            "placa":registro.placa,
            "adjuntos":lista_adjuntos,
            "fecha_estado":registro.fecha_estado
        }
    res=enviar_documentos_estado(historial,body,registro)
    if res:
        historial.info("Se envio correctamente los datos a la api")
        enviar_seguimiento(historial,registro,'actualiza-autohub')
    else:
        raise Exception ('Fallo el envio de los documentos')

def estado_reingresado(historial:Logger,registro:Inmatriculacion):

    historial.title(f'Se procedera a actualizar el sistema del siguiente titulo {registro.titulo} que esta reingresado.')
    body={
                "inmatriculacion":registro.interno,
                "titulo":registro.titulo,
                "tipo":"RE",
                "placa":registro.placa,
                "adjuntos":[],
                "fecha_estado":registro.fecha_estado
            }
    res=enviar_documentos_estado(historial,body,registro)
    if res:enviar_seguimiento(historial,registro,'actualiza-autohub')
    else:raise Exception ('Fallo el envio de los documentos')

def estado_observado(historial:Logger,registro:Inmatriculacion):
    try:
        titulo=registro.titulo
        anio=registro.anio
        #obteniendo documentos
        ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{titulo}-{anio}')
        ruta_archivo=os.path.join(ruta_carpeta,'ESQUELA_OBSERVACION.pdf')
        fecha_vencimiento=obtener_datos_pdf_api(historial,ruta_archivo, titulo)
        if fecha_vencimiento:
            registro.fecha_vencimiento=fecha_vencimiento
            #Se envia el correo
            observacionb64=transformar_b64(ruta_archivo)
            body={
                "inmatriculacion":registro.interno,
                "titulo":registro.titulo,
                "tipo":"OB",
                "placa":registro.placa,
                "adjuntos":[
                    {
                        "tipo":"OBS", "filename":'ESQUELA_OBSERVACION.pdf',"base64":observacionb64
                    }
                ],
                "fecha_estado":registro.fecha_estado
            }
            resp=enviar_documentos_estado(historial,body,registro)
            if resp:enviar_seguimiento(historial,registro,'actualiza-autohub')
            else:raise Exception ('Fallo el envio de los documentos')
        else:
            registro.observacion=f'No se pudo obtener la fecha de vencimiento {titulo} que se encuentra OBSERVADO'
    except Exception as e:
        traceback.print_exc()
        historial.error(f'Fallo en el estado observado. {e}')
        raise e
def estado_liquidado(historial:Logger,registro:Inmatriculacion):
        try:
            titulo=registro.titulo
            anio=registro.anio
            #obteniendo documentos
            ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{titulo}-{anio}')
            ruta_archivo=os.path.join(ruta_carpeta,'ESQUELA_LIQUIDACION.pdf')
            fecha_vencimiento=obtener_datos_pdf_api(historial,ruta_archivo, titulo)
            if fecha_vencimiento:
                registro.fecha_vencimiento=fecha_vencimiento
                #Se envia el correo
                liquidacionb64=transformar_b64(ruta_archivo)
                body={
                    "inmatriculacion":registro.interno,
                    "titulo":registro.titulo,
                    "tipo":"LI",
                    "placa":registro.placa,
                    "adjuntos":[
                        {
                            "tipo":"LIQ", "filename":'ESQUELA_LIQUIDACION.pdf',"base64":liquidacionb64
                        }
                    ],
                    "fecha_estado":registro.fecha_estado
                }
                resp=enviar_documentos_estado(historial,body,registro)
                if resp:enviar_seguimiento(historial,registro,'actualiza-autohub')
            else:raise Exception ('Fallo el envio de los documentos')
        except Exception as e:
            traceback.print_exc()
            historial.error(f'Fallo en el estado observado. {e}')
            raise e
def estado_tachado(historial: Logger, registro:Inmatriculacion, page=None):
    try:
        titulo = registro.titulo
        anio = registro.anio
        # obteniendo documentos
        ruta_carpeta=os.path.join(RUTAPRIN,'download',f'{titulo}-{anio}')
        ruta_archivo=os.path.join(ruta_carpeta,'ESQUELA_TACHA.pdf')
        #Se envia el correo
        tachado64=transformar_b64(ruta_archivo)
        body={
            "inmatriculacion":registro.interno,
            "titulo":registro.titulo,
            "tipo":"TA",
            "placa":registro.placa,
            "adjuntos":[
                {
                    "tipo":"TAC", "filename":'ESQUELA_TACHA.pdf',"base64":tachado64
                }
            ],
            "fecha_estado":registro.fecha_estado
        }
        resp=enviar_documentos_estado(historial,body,registro)
        if resp==200:enviar_seguimiento(historial,registro,'actualiza-autohub')
        else:raise Exception ('Fallo el envio de los documentos')
    except Exception as e:
        historial.error(f'Fallo en el estado tachado. {e}')
        raise e