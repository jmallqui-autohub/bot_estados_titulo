import os
import json
from middleware.googleSheet  import Sheets
from middleware.apis import obtener_lista_procesar
from utils.logger import Logger
from utils.funciones import *
from resources.datosfijos import *
from resources.inmatriculacion import Inmatriculacion
def obtener_datos_sheet(historial:Logger):
    try:
        filtro_bot2=['LISTO','OPENCLOUD']
        filtro_bot3=['PENDIENTE','OBSERVADO','LIQUIDADO','OPENCLOUD','SUSPENDIDO','INCOMPLETO','ERROR','REINGRESADO','ANOTACION']
        idlibro=os.getenv('SHEET_IDLIBRO')
        credenciales_json=os.getenv('SHEET_CREDENCIALES_JOSE')
        credenciales = json.loads(credenciales_json)
        sheets=Sheets(idlibro,credenciales)
        sheets.abrir_hoja('Guia')
        registros= sheets.obtener_datos()
        sheets.abrir_hoja('Prop. Vehicular')
        registro_complementos=sheets.obtener_datos()
        registros_procesar=[]
        for fila, registro in enumerate(registros,start=2):
            body={}
            estadobot2=registro['ESTADO_BOT2']
            estadobot3=registro['ESTADO_BOT3']
            inmatriculacion=registro['Numero_de_inmatriculacion']
            fecha_titulo=registro['Fecha']
            estadosiguelo=registro['Estado Siguelo']
            if estadobot2 in filtro_bot2 and dias_habiles(fecha_titulo):
                if estadobot3 == '':estadobot3='PENDIENTE'
                if estadosiguelo == '':estadosiguelo='EN CALIFICACION'
                if estadobot3 in filtro_bot3:
                    body['fila']=fila
                    body['inmatriculacion']=inmatriculacion
                    body['kardex']=registro['Kardex']
                    body['naturaleza']="virtual"
                    body['servicio']=registro['Tipo_Servicio_Bot1']
                    body['titulo']=registro['Numero de Titulo']
                    body['estadosiguelo']=registro['Estado Siguelo']
                    body['estado']=estadobot3
                    body['fvencimiento']=registro['Fecha Vencimiento( Liquidados y Observados)']
                    body['montoDevolver']=registro['Monto  ( Inscritos y Tachados)']
                    body['codigover']=registro['Codigo_Verificacion']
                    body['hoja_titulo']=registro['Numero de Hoja']
                    body['fecha_presentacion']=registro['Fecha']
                    body['rectificacion']=registro['Rectificacion']
                    body['placa']=registro['Nro.Placa']
                    body['compania']='NO SE SABE'

                    for registros2 in registro_complementos:
                        if inmatriculacion == registros2['numInma']:
                            body['tramite']=registros2['tramite']
                            body['oficina']=registros2['oficina']
                            body['anio']=registros2['anioTitulo']

                    registros_procesar.append(body)
        return registros_procesar
    except Exception as e:
        mensaje=f'Error al obtener los datos del sheets: {e}'
        historial.error(mensaje)
        return ''

def obtener_datos_api(historial:Logger):
    try:
        data=obtener_lista_procesar(historial)
        if  not data:return ''
        registros_apis=data['data']
        sheets=Sheets()
        sheets.abrir_hoja(HOJAGUIA)
        registros= sheets.obtener_datos()
        registros_procesar=[]
        for fila, registro in enumerate(registros,start=2):
            inmatriculacion=Inmatriculacion()
            estadobot2=registro['ESTADO_BOT2']
            estadobot3=registro['ESTADO_BOT3']
            interno=registro['Numero_de_inmatriculacion']
            fecha_titulo=registro['Fecha']
            estadosiguelo=registro['Estado Siguelo']
            if estadobot2 in FILTRO_BOT2 and dias_habiles(fecha_titulo):
                if estadobot3 == '':estadobot3='PENDIENTE'
                if estadosiguelo == '':estadosiguelo='EN CALIFICACION'
                if estadobot3 in FILTRO_BOT3:
                    for registro_api in registros_apis:
                        if str(registro_api['tramite'])==str(interno) and str(registro_api['titulo']).replace('\r','').replace('\n','')  == str(registro['Numero de Titulo']):
                            inmatriculacion.fila=fila
                            inmatriculacion.interno=str(registro_api['tramite'])
                            inmatriculacion.kardex=str(registro_api['kardex'])
                            inmatriculacion.titulo=registro_api['titulo']
                            inmatriculacion.estado_siguelo=registro_api['estado_sunarp']
                            inmatriculacion.estado=estadobot3
                            inmatriculacion.fecha_vencimiento=registro_api['fecha_vencimiento'] if registro_api['fecha_vencimiento'] else registro['Fecha Vencimiento( Liquidados y Observados)']
                            inmatriculacion.monto_devolver=registro_api['monto_devolver'] if registro_api['monto_devolver'] else registro['Monto  ( Inscritos y Tachados)']
                            inmatriculacion.codigo_verificacion=registro_api['codigo_verificacion'] if registro_api['codigo_verificacion'] else registro['Codigo_Verificacion']
                            inmatriculacion.hoja_titulo=registro['Numero de Hoja']
                            inmatriculacion.fecha_presentacion=cambiar_formato_fecha(registro_api['titulo_fecha'])
                            inmatriculacion.rectificacion=registro_api['rectificacion']
                            inmatriculacion.placa=registro['Nro.Placa']
                            inmatriculacion.tramite=registro_api['tipo_tramite']
                            inmatriculacion.oficina=registro_api['oficina_registral']
                            inmatriculacion.anio=registro_api['anio']
                            inmatriculacion.compania=registro_api['compania']
                            registros_procesar.append(inmatriculacion)
        return registros_procesar
    except Exception as e:
        mensaje=f'Error al obtener los datos de la API: {repr(e)}'
        historial.error(mensaje)
        return ''

def actualizar_datos_sheet(historial:Logger,registro:Inmatriculacion):
    fila=registro.fila
    try:
        sheets=Sheets()
        sheets.abrir_hoja(HOJAGUIA)
        col_inicial1='Q'
        col_final1='V'
        estadosiguelo=registro.estado_siguelo
        fvencimiento=registro.fecha_vencimiento
        monto=registro.monto_devolver
        codigo=registro.codigo_verificacion
        if registro.observacion:observacion=registro.observacion
        else:observacion=''
        estado=registro.estado
        if registro.placa:placa=registro.placa
        else:placa=''
        celda=f'{col_inicial1}{fila}:{col_final1}{fila}'
        celda1=f'Y{fila}:Y{fila}'
        tupla_datos=[[estadosiguelo,fvencimiento,monto,observacion,codigo,estado]]
        tupla_datos2=[[placa]]
        sheets.updateCeldas(celda,tupla_datos)
        if registro.estado =='INCOMPLETO':
            formato_color = {
                "backgroundColor": {
                    "red": 1.0,    # 0.0 a 1.0
                    "green": 0.0,
                    "blue": 0.0
                }
            }
            sheets.colorear_celda(celda,formato_color)
            historial.obs('Se hizo el cambio de color')
        if registro.estado =='ERROR':
            formato_color = {
                "backgroundColor": {
                    "red": 0.0,    # 0.0 a 1.0
                    "green": 0.0,
                    "blue": 1.0
                }
            }
            sheets.colorear_celda(celda,formato_color)
            historial.obs('Se hizo el cambio de color')
        if placa:sheets.updateCeldas(celda1,tupla_datos2)
        historial.info(f'Se actualizo la fila {fila}')
    except Exception as e:
        mensaje=f'Error al actualizar la fila {fila}, estado de la placa en {registro['estado']}. {e}'
        historial.error(mensaje)

def obtener_casos_fallidos(historial:Logger,registros_procesar:list):
    try:
        lista_procesar=[]
        registro_fallidos=obtener_data_bitacora()
        for registros in registros_procesar:
            inmatriculacion=str(registros['inmatriculacion'])
            if inmatriculacion in registro_fallidos and registro_fallidos[inmatriculacion]['intentos']==1:
                lista_procesar.append(registros)
        return lista_procesar
    except Exception as e:
        historial.error(f'Error al obtener la lista de consultas fallidas. {e}')
        return []


def obtener_registros_api(historial:Logger)-> list:
    casos_procesar=[]
    try:
        casos=obtener_casos_api(historial)
        if len(casos)>0:
            for caso in casos:
                inmatriculacion=Inmatriculacion()
                # Se registra los primeros datos del tramite
                inmatriculacion.interno= caso['tramit_id']
                inmatriculacion.titulo= caso['referencia']
                inmatriculacion.id= caso['id']
                inmatriculacion.bot=os.getenv('BOT_ID')
                datos_inmatriculacion=obtener_datos_tramite(historial,inmatriculacion)
                if len(datos_inmatriculacion)>0:
                    # Se completa los demas datos para el tramite
                    data=datos_inmatriculacion[0]
                    inmatriculacion.kardex=data['kardex']
                    inmatriculacion.compania=data['compania']
                    inmatriculacion.fecha_presentacion=data['fecha_presentacion']
                    inmatriculacion.anio=str(data['titulo_anio']).strip()
                    inmatriculacion.oficina=str(data['oficina_registral']).strip()
                    inmatriculacion.codigo_verificacion=data['codigo_verificacion']
                    inmatriculacion.estado_siguelo=data['estado_titulo_siguelo']
                    inmatriculacion.estado_autohub=data['estado_titulo_autohub']
                    inmatriculacion.titulo_tipo=data['titulo_tipo']
                    casos_procesar.append(inmatriculacion)
        return casos_procesar
    except Exception as e:
        historial.error(f'Error en la obtencion de los casos para procesar. {e}')
        return casos_procesar