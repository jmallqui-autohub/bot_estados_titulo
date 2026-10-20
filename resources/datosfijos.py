import os
# Ruta del directorio principal
RUTAPRIN=os.path.dirname(os.path.dirname(__file__))

# Lista de correos para las notificaciones de errores
CORREOS_ERROR='jmallqui@autohub.pe,practicantes.sistemas@notariapaino.pe'

# Rutas de los tokens de los correos
RUTA_TOKEN=os.path.join(RUTAPRIN,'resources','token.json')
RUTA_TOKEN2=os.path.join(RUTAPRIN,'resources','token2.json')
RUTA_TOKEN3=os.path.join(RUTAPRIN,'resources','token3.json')

# Ruta de la imagen del Logo
RUTA_LOGO=os.path.join(RUTAPRIN,'resources','logo.jpeg')

# Ruta de los Json de uso del bot
RUTA_BITACORA=os.path.join(RUTAPRIN,'resources','bitacora.json')
RUTA_TACHADO=os.path.join(RUTAPRIN,'resources','tachados.json')

# Permisos de los correos
SCOPES=["https://www.googleapis.com/auth/gmail.send","https://www.googleapis.com/auth/gmail.readonly"]
SCOPES2=['https://www.googleapis.com/auth/gmail.readonly']
SCOPES3=['https://www.googleapis.com/auth/gmail.send']

# Listas de correos dependiendo el tipo de notificacion
CORREOS_LIQUIDADOS='jmallqui@notariapaino.pe,p.jesus@notariapaino.pe,practicantes.sistemas@notariapaino.pe,asistente@autohub.pe'
CORREOS_OBSERVADOS='jmallqui@notariapaino.pe,p.jesus@notariapaino.pe,asistente@autohub.pe'
CORREOS_RECLAMOS='administracion@autohub.pe,atenciondefensorbienesmuebles_lima@sunarp.gob.pe,practicantes.sistemas@notariapaino.pe,asistenteadm@autohub.pe,soporte2@autohub.pe,soporte3@autohub.pe,mesadeayuda_lima@sunarp.gob.pe,enlinea@sunarp.gob.pe,jmallqui@autohub.pe,asistente@autohub.pe,p.jesus@notariapaino.pe,jrojas@sunarp.gob.pe'

# Ruta del disco G
RUTA_DISCO=r"\\192.168.48.6"
RUTA_PDF=os.path.join(RUTA_DISCO,'archivos','RobotFiles')

# Nombres de las hojas
HOJAGUIA='Guia'

# Listas de filtros para procesar
FILTRO_BOT2=['LISTO','OPENCLOUD']
FILTRO_BOT3=['PENDIENTE','OBSERVADO','LIQUIDADO','OPENCLOUD','SUSPENDIDO','INCOMPLETO','ERROR','ANOTACION','REINGRESADO']

# Listas de cabeceras del titulo siguelo
LISTA_CABECERA_TITULO=['Partida','Asientos','Placa','TIVe','O.Giro']

#cabeceras_bot3
CESTSIGUELO='Estado Siguelo'
CFCHVENCIMIENTO='Fecha Vencimiento( Liquidados y Observados)'
CMONTO='Monto  ( Inscritos y Tachados)'
COBS3='Observaciones_bot3'
CCODVERI='Codigo_Verificacion'
CBOT3='ESTADO_BOT3'
CPLACA='Nro.Placa'
CBOT4='ESTADO_BOT4'

# Lista de mensaje de error en la consulta del Siguelo
LISTA_MENSAJES_SIGUELO=['Por favor seleccione la Oficina Registral','Por favor seleccione el Año del Título','Por favor ingrese el Número del Título','Por favor ingrese el código captcha del Título']

# Diccionario segun el tramite Opencloud
tipo_tramite={
    "ACTA":'A',
    "BLOQUEO":'B',
    "BÚSQUEDA":'BQ',
    "C/S DE PARTE":'SP',
    "C/S DE TIT. ARC.":'ST',
    "CERT. NEGATIVO":'CN',
    "CERT. POSITIVO":'CP',
    "COPIA LITERAL":'CL',
    "CRI":'CR',
    "DUPLIC. TARJETA":'DT',
    "GRAVAMEN":'G',
    "LEV. BLOQUEO":'LB',
    "OTROS":'OS',
    "PARTE":'P',
    "PLACA":'PL',
    "RESERVA NOMBRE":'R',
    "VIGENCIA PER. JUR.":'VJ',
    "VIGENCIA POD.":'VP'
}

# diccionario segun el estado del titulo OpenCloud
tipo_estado_titulo={
    "APELADO":'29',
    "DEVOLUCION SOLICITADA":'20',
    "DEVUELTO":'18',
    "EXPEDIDO":'19',
    "INSCRITO":'10',
    "LIQUIDADO":'11',
    "OBSERVADO":'7',
    "PAGADO":'15',
    "POR DEVOLVER":'17',
    "PRESENTADO":'12',
    "RECLAMO LIQ.":'25',
    "REING. PARA TACHA":'26',
    "REINGRESADO":'9',
    "SUSPENDIDO":'23',
    "TACHADO":'8',
    "TACHADO P/FALTA DE PAGO":'28'
}

# Diccionario segun las oficinas registrales Opencloud
OFICINAS = {
    "ANDAHUAYLAS": "001",
    "ABANCAY": "002",
    "AREQUIPA": "003",
    "AYACUCHO": "004",
    "BARRANCA": "005",
    "BAGUA": "006",
    "CALLAO": "007",
    "CAJAMARCA": "008",
    "CAMANA": "009",
    "CAÑETE": "010",
    "CASMA": "011",
    "CASTILLA  APLAO": "012",
    "CHACHAPOYAS": "013",
    "CHEPEN": "014",
    "CHICLAYO": "015",
    "CHIMBOTE": "016",
    "CHINCHA": "017",
    "CHOTA": "018",
    "CORONEL PORTILLO": "019",
    "CUSCO": "020",
    "HUACHO": "021",
    "HUAMACHUCO": "022",
    "HUANCAVELICA": "023",
    "HUANCAYO": "024",
    "HUANTA": "025",
    "HUANUCO": "026",
    "HUARAL": "027",
    "HUARAZ": "028",
    "ICA": "029",
    "ILO": "030",
    "IQUITOS": "031",
    "ISLAY  MOLLENDO": "032",
    "JAEN": "033",
    "JUANJUI": "034",
    "JULIACA": "035",
    "LIMA": "036",
    "MADRE DE DIOS": "037",
    "MOQUEGUA": "038",
    "MOYOBAMBA": "039",
    "NAZCA": "040",
    "OTUZCO": "041",
    "PASCO": "042",
    "PISCO": "043",
    "PIURA": "044",
    "PUNO": "045",
    "QUILLABAMBA": "046",
    "SAN PEDRO DE LLOC": "047",
    "SATIPO": "048",
    "LA MERCED (SELVA CENTRAL)": "062",  # Sobrescribe el valor anterior ("049")
    "SICUANI": "050",
    "SULLANA": "051",
    "TACNA": "052",
    "TARAPOTO": "053",
    "TARMA": "054",
    "TINGO MARIA": "055",
    "TRUJILLO": "056",
    "TUMBES": "057",
    "YURIMAGUAS": "058",
    "RENIEC": "059",
    "PUCALLPA": "060",
    "MAYNAS": "061"
}

ETIQUETAS = {
    "INSCRITO": { 'label': 'INSCRITO', 'id_etiqueta': 'Label_8050537850410272083'},
    "TACHADO": { 'label': 'DENEGADO', 'id_etiqueta': 'Label_924364492624745975'},
    "OBSERVADO": { 'label': 'OBSERVADO', 'id_etiqueta': 'Label_934586347858973474'},
    "LIQUIDADO": { 'label': 'LIQUIDADO', 'id_etiqueta': 'Label_970498702782289693'},
}

ESTADOS = {
    "INSCRITO": "10",
    "LIQUIDADO": "11",
    "TACHADO": "8",
    "OBSERVADO": "7"
}

# Diccionario segun codigo de empresa
COMPANIAS={
    "20347764664":"AUTOLAND",
    "20613170716":"PANGU",
    "EUROMOTORSS1":"EUROSHOP",
    "EUROMOTORSS2":"REVOSHOP",
    "20600053273":"MAQALFA",
    "20602780466":"MAQGAMA",
    "20602796524":"MAQBETA",
    "20606691883":"MAQDELTA",
    "20606692588":"MAQSIGMA",
    "20160286068":"MAQUINARIAS",
    "EUROMOTORS":"EUROMOTORS",
    "20559968499":"COMINKA MOTORS",
    "20491555140":"MUNDOMOTRIZ",
    "20608061909":'SMART CARGO',
    "20124148970":"MAQUIMAS",
    "20524207509":"ASTARA",
    "20601960762":"LEON AUTOS",
    "20453919651":"PERU MOTOR",
    "20536579746":"BJR GRUPO",
    "20502797230":"DIVEIMPORT"
}

# Listas de Feriados 2026
LISTA_FERIADOS= [
        "2026-01-01",  # Año Nuevo
        "2026-04-02",  # Jueves Santo
        "2026-04-03",  # Viernes Santo
        "2026-05-01",  # Día del Trabajo
        "2026-06-07",  # Batalla de Arica
        "2026-06-29",  # San Pedro y San Pablo
        "2026-07-23",  # Día de la FAP
        "2026-07-27",  # Fiestas Patrias
        "2026-07-28",  # Fiestas Patrias
        "2026-07-29",  # Fiestas Patrias
        "2026-08-06",  # Batalla de Junín
        "2026-08-30",  # Santa Rosa de Lima
        "2026-10-08",  # Combate de Angamos
        "2026-11-01",  # Todos los Santos
        "2026-12-08",  # Inmaculada Concepción
        "2026-12-09",  # Batalla de Ayacucho
        "2026-12-25",  # Navidad
    ]