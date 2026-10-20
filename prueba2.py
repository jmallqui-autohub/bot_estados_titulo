import time
import os
import traceback
from dotenv import load_dotenv
from middleware.funciones_correo import *
from middleware.apis import *
from utils.funciones import obtener_datos_inscripcionV2,calcular_dias_habiles
from utils.html import *
from resources.datosfijos import *
from utils.logger import Logger
from middleware.funciones_correo import *
from utils.funciones_sheet import obtener_datos_sheet
from bot.SUNARP.Sprl_Sid.sprl import consulta_sprl
if __name__ =='__main__':
    try:
        load_dotenv()
        historial=Logger('PRUEBA')
        ruta=os.path.join(RUTAPRIN,'asiento500.pdf')
        # fecha='31/10/2025'
        # resp,dias_habiles=calcular_dias_habiles(fecha)
        # asunto=f'RECLAMO TITULO 2025 - 3155233/ K-8888'
        # mensaje_autohub=generar_html_reclamos('20/10/2025','3155233','2025')
        # enviar_correo(CORREOS_ERROR,asunto,mensaje_autohub,2,'','',historial,html=True)
        obtener_datos_inscripcionV2(historial,ruta)
    except Exception as e:
        traceback.print_exc()
        historial.error(f'Error: {e}')

