
from utils.logger import Logger
from middleware.funciones_correo import *
from bot.LECTURAPDF.estados_funciones import estado_inscrito,estado_observado,estado_tachado
from bot.SUNARP.Sprl_Sid.sprl import consulta_sprl
from datetime import datetime
def proceso_pdf(historial:Logger,registro):
    titulo=registro['titulo']
    historial.obs(f'Iniciando con la obtencion del estado del titulo {titulo}')
    #estado=obtener_estado_siguelo(historial,registro)
    respuesta=consulta_sprl(historial,registro)
    if not respuesta:
        registro['observacion']=f'No se encontro el estado del titulo {titulo} en el sprl'
        return False
    estado=str(registro['estadosiguelo']).strip().upper()
    historial.info(f'Estado encontrado: {estado}')
    match estado:
        case 'INSCRITO': estado_inscrito(historial,registro)
        case 'OBSERVADO': estado_observado(historial,registro)
        case 'TACHADO': pass #estado_tachado(historial,registro)
        case 'LIQUIDADO': pass
        case _: registro['estado']='PENDIENTE'



        





