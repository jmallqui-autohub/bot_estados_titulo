import os
import json
import base64
import email
import re
from resources.datosfijos import *
from utils.logger import Logger
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def enviar_correo(to,subject,mensaje,propietario,cc,cco,ruta_archivos,historial:Logger,html=False,):
    try:
        credenciales=None
        #PARTE PARA VALIDAR EL CORREO
        if propietario ==1:
            #Credenciales de robot
            ruta_token=RUTA_TOKEN
            correo_credenciales=os.getenv('EMAIL_CREDENTIALS')
            correo_credenciales=json.loads(correo_credenciales)
            scopes=SCOPES
        elif propietario==2:
            #Credenciales autohub administrador
            ruta_token=RUTA_TOKEN3
            correo_credenciales=os.getenv('EMAIL_CREDENCIALES_ADMINISTRADOR')
            correo_credenciales=json.loads(correo_credenciales)
            scopes=SCOPES
        else:
            #Credenciales autohub
            ruta_token=RUTA_TOKEN2
            correo_credenciales=os.getenv('EMAIL_CREDENTIALS_AUTOHUB')
            correo_credenciales=json.loads(correo_credenciales)
            scopes=SCOPES3
        if os.path.exists(ruta_token):
            credenciales=Credentials.from_authorized_user_file(ruta_token,scopes)
        else:
            flow=InstalledAppFlow.from_client_config(correo_credenciales,scopes)
            credenciales=flow.run_local_server(port=0)
            with open(ruta_token,'w') as token:
                token.write(credenciales.to_json())
        service=build('gmail','v1',credentials=credenciales)
        # PARTE PARA GENERAR EL CORREO
        message=MIMEMultipart('related')
        if propietario==1:
            message['Subject']=subject
            message['To']= to
        else:
            alias="AutoHub"
            correo_emisor="asistente@autohub.pe"
            message = MIMEMultipart("related")
            message["From"] = f"{alias} <{correo_emisor}>"
            message["Subject"] = subject
            message["To"] = to
            message["cc"]=cc
        message["Bcc"]=cco
        if html:message.attach(MIMEText(mensaje,"html"))
        else:message.attach(MIMEText(mensaje,"plain"))
        if ruta_archivos:
            for pdf in ruta_archivos:
                pdf_filename=os.path.basename(pdf)
                with open(pdf, "rb") as pdf_file:
                    pdf_part = MIMEApplication(pdf_file.read(), _subtype="pdf")
                    pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
                    message.attach(pdf_part)
        raw_message=base64.urlsafe_b64encode(message.as_bytes()).decode()
        body={"raw":raw_message}
        service.users().messages().send(userId="me",body=body).execute()
        historial.info('Se envio el correo')
    except Exception as e:
        mensaje=f'Error al enviar el correo. {e}'
        historial.error(mensaje)
def getNroCodigo(text):
    ref1 = text.index("ingresando el")
    ref2 = text.index("de placa(s")
    text= text[ref1:ref2]
    palabras = text.split()
    for palabra in palabras:
        try:
            codigo = int(palabra)
            return palabra
        except:
            pass
    return ""
def get_placa(text):
    ref1 = text.index("de placa(s)")
    ref2 = text.index("Si tuviera")
    text= text[ref1:ref2]
    palabras = text.split()
    placa=palabras[3]
    placa=str(placa).replace('<br>','').strip()
    return placa
def obtener_mensaje(service, msg_id):
    # tomar la instancia del mensaje
    message = service.users().messages().get(userId='me', id=msg_id,format='raw').execute()

    msg_str = base64.urlsafe_b64decode(message['raw'].encode("utf-8")).decode("utf-8")
    mime_msg = email.message_from_string(msg_str)
    # compruebe si el contenido es de varias partes (normalmente lo es) 
    content_type = mime_msg.get_content_maintype()
    if content_type == 'multipart':
        # generalmente habrá 2 partes, la primera será el cuerpo en el texto
        # el segundo será el texto en html 
        parts = mime_msg.get_payload()

        # retorna el texto codificado 
        final_content = parts[0].get_payload()
        return final_content
    elif content_type == 'text':
        return mime_msg.get_payload()
    else:
        return ""
def obtener_mensaje2(service, msg_id):
    # tomar la instancia del mensaje
    message = service.users().messages().get(userId='me', id=msg_id).execute()
    payload=message.get('payload')
    # Buscar en las partes del mensaje
    parts = payload.get('parts', [])
    for part in parts:
        if part.get('mimeType') == 'text/plain':
            data = part.get('body', {}).get('data')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
    
    # Si no se encontró en las partes, buscar en el cuerpo principal
    if payload.get('mimeType') == 'text/plain':
        data = payload.get('body', {}).get('data')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
    
    return ''

def obtener_codigo_verificacion(placa,registro,historial:Logger):
    credenciales=None
    anio=registro['anio']
    titulo=registro['titulo']
    if len(titulo) !=8:
        titulo = str(titulo).zfill(8)
    correo_credenciales=os.getenv('EMAIL_CREDENTIALS')
    correo_credenciales=json.loads(correo_credenciales)
    if registro['codigover']!='' and registro['codigover']!='NO ENCONTRADO':
        return registro['codigover']
    if os.path.exists(RUTA_TOKEN):
        credenciales=Credentials.from_authorized_user_file(RUTA_TOKEN,SCOPES)
    if not credenciales or not credenciales.valid:
        if credenciales and credenciales.expired and credenciales.refresh_token:
            credenciales.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_config(correo_credenciales,SCOPES)
            credenciales=flow.run_local_server(port=0)
        with open(RUTA_TOKEN,'w') as token:
            token.write(credenciales.to_json())
    service =build('gmail','v1',credentials=credenciales)
    #buscar_ids_correos=service.users().messages().list(userId='me',q=f'TIVE {placa}').execute()
    buscar_ids_correos=service.users().messages().list(userId='me',q=f'TIVE {anio}-{titulo}').execute()
    if buscar_ids_correos['resultSizeEstimate']>0:
        historial.obs('Se encontraron correos')
        ids= buscar_ids_correos['messages']
        primerId=ids[0]['id']
        texto=obtener_mensaje(service,primerId)
        if texto:
            codigo_verificacion=getNroCodigo(str(texto))
            mensaje=f"Codigo verificacion encontrado para placa {placa}: {codigo_verificacion}"
            historial.info(mensaje)
            return str(codigo_verificacion)
        else: return False
    else:
        titulo=registro['titulo']
        kardex=registro['kardex']
        asunto='URGENTE- BOT3 INMATRICULACION'
        mensaje=f'No se envio el codigo de verificacion. \nPlaca: {placa} Kardex: {kardex} titulo{titulo}'
        enviar_correo(CORREOS_ERROR,asunto,mensaje,1,'','',False,historial) 
        return False
def obtener_nro_placa(registro,historial:Logger):
    credenciales=None
    anio=registro['anio']
    titulo=registro['titulo']
    if len(titulo) !=8:
        titulo = str(titulo).zfill(8)
    correo_credenciales=os.getenv('EMAIL_CREDENTIALS')
    correo_credenciales=json.loads(correo_credenciales)
    if os.path.exists(RUTA_TOKEN):
        credenciales=Credentials.from_authorized_user_file(RUTA_TOKEN,SCOPES)
    if not credenciales or not credenciales.valid:
        if credenciales and credenciales.expired and credenciales.refresh_token:
            credenciales.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_config(correo_credenciales,SCOPES)
            credenciales=flow.run_local_server(port=0)
        with open(RUTA_TOKEN,'w') as token:
            token.write(credenciales.to_json())
    service =build('gmail','v1',credentials=credenciales)
    buscar_ids_correos=service.users().messages().list(userId='me',q=f'TIVE {anio}-{titulo}').execute()
    if buscar_ids_correos['resultSizeEstimate']>0:
        historial.obs('Se encontraron correos')
        ids= buscar_ids_correos['messages']
        primerId=ids[0]['id']
        texto=obtener_mensaje(service,primerId)
        if texto:
            placa=get_placa(str(texto))
            mensaje=f"Placa encontrada {placa}"
            historial.info(mensaje)
            return str(placa)
        else: return False
    else:
        titulo=registro['titulo']
        kardex=registro['kardex']
        asunto='URGENTE- BOT3 INMATRICULACION'
        mensaje=f'No se obtuvo la placa . \n Kardex: {kardex} titulo{titulo}'
        enviar_correo(CORREOS_ERROR,asunto,mensaje,1,'','',False,historial) 
        return False
def obtener_estado_siguelo(historial:Logger,registro:dict):
    credenciales=None
    correo_credenciales=os.getenv('EMAIL_CREDENTIALS')
    correo_credenciales=json.loads(correo_credenciales)
    hoja_titulo=registro['hoja_titulo']
    anio=registro['anio']
    titulo=registro['titulo']
    if os.path.exists(RUTA_TOKEN):
        credenciales=Credentials.from_authorized_user_file(RUTA_TOKEN,SCOPES)
    if not credenciales or not credenciales.valid:
        if credenciales and credenciales.expired and credenciales.refresh_token:
            credenciales.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_config(correo_credenciales,SCOPES)
            credenciales=flow.run_local_server(port=0)
        with open(RUTA_TOKEN,'w') as token:
            token.write(credenciales.to_json())
    service =build('gmail','v1',credentials=credenciales)
    buscar_ids_correos=service.users().messages().list(userId='me',q=f'{anio}-{hoja_titulo}',maxResults=1).execute()
    #print(buscar_ids_correos)
    if buscar_ids_correos['resultSizeEstimate']>0:
        historial.obs('Se encontraron correos')
        ids= buscar_ids_correos['messages']
        id=ids[0]['id']
        registro['id']=id
        texto_correo=obtener_mensaje(service,id)
        if texto_correo:
            print(1)
            if re.search(r'\bINSCRITO\b', texto_correo, re.IGNORECASE):estado='INSCRITO'
            elif re.search(r'\bOBSERVADO\b', texto_correo, re.IGNORECASE):estado='OBSERVADO'
            elif re.search(r'\bLIQUIDADO\b', texto_correo, re.IGNORECASE):estado='LIQUIDADO'
            elif re.search(r'\bDENEGADO\b', texto_correo, re.IGNORECASE):estado='TACHADO'
            else:estado=''
            estado_siguelo=estado
            if estado_siguelo:return estado_siguelo
            else:
                print(2)
                if len(titulo) !=8:
                    titulo = str(titulo).zfill(8)
                buscar_ids_correos=service.users().messages().list(userId='me',q=f'TIVE {anio}-{titulo} ').execute()
                if buscar_ids_correos['resultSizeEstimate']!=0: return 'INSCRITO'
                else:return False
        else: return False
    elif titulo:
        print(2)
        if len(titulo) !=8:
            titulo = str(titulo).zfill(8)
        buscar_ids_correos=service.users().messages().list(userId='me',q=f'TIVE {anio}-{titulo}').execute()
        if buscar_ids_correos['resultSizeEstimate']!=0: return 'INSCRITO'
        else:return False
    else:
        print(3)
        historial.obs('No se encontraron correos')
        return False

def obtener_enlace_pdf(historial:Logger,registro:dict):
    credenciales=None
    correo_credenciales=os.getenv('EMAIL_CREDENTIALS')
    correo_credenciales=json.loads(correo_credenciales)
    anio=registro['anio']
    titulo=registro['titulo']
    if len(titulo) !=8:
        titulo = str(titulo).zfill(8)
    if os.path.exists(RUTA_TOKEN):
        credenciales=Credentials.from_authorized_user_file(RUTA_TOKEN,SCOPES)
    if not credenciales or not credenciales.valid:
        if credenciales and credenciales.expired and credenciales.refresh_token:
            credenciales.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_config(correo_credenciales,SCOPES)
            credenciales=flow.run_local_server(port=0)
        with open(RUTA_TOKEN,'w') as token:
            token.write(credenciales.to_json())
    service =build('gmail','v1',credentials=credenciales)
    buscar_ids_correos=service.users().messages().list(userId='me',q=f'{anio}-{titulo}',maxResults=1).execute()
    if buscar_ids_correos['resultSizeEstimate']>0:
        historial.obs('Se encontraron correos')
        link=''
        ids= buscar_ids_correos['messages']
        id=ids[0]['id']
        registro['id']=id
        texto_correo=obtener_mensaje2(service,id)
        patron_esquela = r'https://enlinea\.sunarp\.gob\.pe/sunarpweb/pages/extranet/VerEsquela\.faces\?state=mostrarEsquela&refnumtitu=\d+&tipoesquela=[A-Z]&arearegid=\d+'
        match_esquela = re.search(patron_esquela, texto_correo, re.IGNORECASE)
        if match_esquela:link=match_esquela.group(0)
        return link
    else:return None
