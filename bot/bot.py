import traceback
import time
import os
from utils.logger import Logger
from utils.funciones import verificar_hora_ejecucion
from playwright.sync_api import Page
from bot.SUNARP.SigueloCamoufox.siguelo import proceso_siguelo
from bot.OPCLOUD.opcloud import proceso_opcloud
from resources.datosfijos import *
from utils.funciones_sheet import actualizar_datos_sheet
from resources.inmatriculacion import Inmatriculacion
from middleware.apis import enviar_seguimiento
def proceso_bot(registros:list[Inmatriculacion], historial: Logger, page: Page,browser):
    total_consultas = len(registros)

    for index, registro in enumerate(registros):
        try:
            historial.obs(f'Consulta nro {index + 1} de {total_consultas}')
            historial.debug(f'>> Kardex: {registro.kardex}', condicion=True)
            historial.debug(f'>> Inmatriculacion: {registro.interno}', condicion=True)
            historial.debug(f'>> Titulo: {registro.titulo}', condicion=True)
            historial.debug(f'>> Oficina: {registro.oficina}', condicion=True)
            historial.debug(f'>> Compania: {registro.compania}', condicion=True)
            historial.debug(f'>> Estado Siguelo: {registro.estado_siguelo}', condicion=True)
            enviar_seguimiento(historial,registro,'inicia-proceso')
            page=proceso_siguelo(registro, historial, page,browser)
            if not verificar_hora_ejecucion():
                historial.info("Fuera de horario. Cerrando...")
                return page
        except Exception as e:
            traceback.print_exc()
            mensaje = f'Error en el proceso del bot: {e}'
            historial.error(mensaje)
    return page
