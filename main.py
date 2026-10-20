import time as tiempo
import sys
import os
from dotenv import load_dotenv
from utils.funciones_sheet import *
from utils.funciones import *
from bot.bot import proceso_bot
from utils.logger import Logger
from resources.datosfijos import *
from datetime import datetime 
from pathlib import Path
import traceback    
from camoufox.sync_api import Camoufox
from playwright.sync_api import Error as PlaywrightError
from playwright._impl._errors import TargetClosedError

if __name__ =='__main__':
    load_dotenv()
    try:
        bot_asignado=os.getenv('BOT_ASIGNADO')
        perfil = Path("profiles/camoufox")
        perfil.mkdir(parents=True, exist_ok=True)
        historial=Logger(bot_asignado)
        cont=0
        historial.title('######################### INICIANDO BOT ############################')
        historial.debug(f'Hora Inicio: {datetime.now().time()}')
        if not verificar_hora_ejecucion():historial.obs('Hora de descanso del bot')
        else:
            while True:
                try:
                    with Camoufox(os="windows",locale="es-PE",humanize=True,headless=False,persistent_context=True,user_data_dir=str(perfil), window=(900, 700)) as browser:
                        page=browser.new_page()
                        while True:
                            # Obtenemos lso registros para procesar
                            registros=obtener_registros_api(historial)
                            cont+=1
                            if registros and len(registros)>0:
                                #RECORRIDO NORMAL
                                page=proceso_bot(registros, historial, page,browser)
                            else:
                                historial.info('No hay casos para procesar')
                                tiempo.sleep(3)
                                raise Exception('Entrando a tiempo de espera')
                            if cont==20:
                                historial.obs('reiniciando el navegador')
                                break
                except Exception as t:
                    tiempo.sleep(300)
                    historial.obs('volviendo a iniciar el navegador')
                tiempo.sleep(5)
        historial.title('===========PROGRAMA FINALIZADO ===========')
        historial.debug(f'Hora Fin: {datetime.now().time()}')
    except Exception as e:
        mensaje=f'Error en el proceso del bot: {repr(e)}'
        traceback_str = traceback.format_exc()
        historial.error(f'{mensaje}\n{traceback_str}')

    