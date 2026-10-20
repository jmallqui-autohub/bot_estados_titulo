import time
import re
import os
from playwright.sync_api import Page
from utils.logger import Logger
from resources.inmatriculacion import Inmatriculacion
from datetime import datetime as dt
from resources.datosfijos import *
from middleware.apis import *

def descargar_esquela_fechaEstado(page: Page, registro:Inmatriculacion, historial:Logger):
    try:
        ruta_carpeta = os.path.join(RUTAPRIN, 'download', f'{registro.titulo}-{registro.anio}')
        os.makedirs(ruta_carpeta, exist_ok=True)
        nombre_archivo=''
        match registro.estado_siguelo:
            case 'OBSERVADO':
                nombre_archivo='ESQUELA_OBSERVACION.pdf'
            case 'LIQUIDADO':
                nombre_archivo='ESQUELA_LIQUIDACION.pdf'
            case 'TACHADO':
                nombre_archivo='ESQUELA_TACHA.pdf'
            case _:
                historial.info(f'Caso de {"Inscripcion" if registro.estado_siguelo =="INSCRITO" else "Reingreso"}')
        # Boton de Detalle del Seguimiento
        page.locator('body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(1) > td > a > span').click()

        cont = 0
        lista_casos_encontrados = []
        # Iteramos hoja por hoja hasta encontrar casos que cumplan con los solicitado
        while True:
            cont += 1

            # Se espera la tabla y se obtiene el nro de filas encontradas
            page.wait_for_selector('#gridDiv > table > tbody', timeout=10000)
            nro_filas = page.locator('#gridDiv > table > tbody > tr').count()
            historial.debug(f'Numero de filas encontradas: {nro_filas} en la pagina {cont}')

            # Se itera fila por fila
            for i in range(nro_filas):
                etapa = page.locator(f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(2) > p').inner_text().upper().strip()
                valor_estado = page.locator(f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(3) > p:nth-child(2) > span').inner_text().upper().strip()
                if valor_estado == registro.estado_siguelo and 'SECCION REGISTRAL' in etapa:
                    valor = page.locator(f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(5)')
                    if valor.count() > 0:
                        lista_casos_encontrados.append({
                            'pagina': cont,
                            'fila': i + 1,
                            'selector': f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(5) > div > a',
                            'selector_fecha':f'#gridDiv > table > tbody > tr:nth-child({i+1}) > td:nth-child(4)>p:nth-child(1)',
                            'etapa': etapa
                        })
                        historial.obs(f'caso {registro.estado_siguelo} encontrado en la página {cont}, fila {i+1}, etapa {etapa}')

            #Se verifica si existe otra hoja para su busqueda
            selector_btn_sig = 'body > div:nth-child(3) > div.col-sm-9 > div > div.nav-div > div > pagination-controls > pagination-template > ul > li.pagination-next.ng-star-inserted'
            lista_boton_siguiente = page.locator(selector_btn_sig)
            if lista_boton_siguiente.count() > 0:
                boton_siguiente = lista_boton_siguiente.first
                clases = boton_siguiente.get_attribute('class') or ''
                esta_deshabilitado = 'disabled' in clases
                if not esta_deshabilitado and boton_siguiente.is_enabled():
                    historial.debug('Avanzando a la siguiente página...')
                    boton_siguiente.click()
                    time.sleep(1)
                else:
                    historial.info('Botón siguiente deshabilitado - No hay más páginas')
                    break
            else:
                historial.info('No se encontró botón siguiente - Finalizando búsqueda')
                break

        #Verificamos si se encontro resultados
        if len(lista_casos_encontrados)>0:
            historial.info(f'Total de casos encontrados: {len(lista_casos_encontrados)}')
            ultimo_caso = lista_casos_encontrados[-1]
            historial.obs(f'Descargando el último observado: Página {ultimo_caso["pagina"]}, Fila {ultimo_caso["fila"]}')

            # Navegar a la página correcta si es necesario
            if ultimo_caso['pagina'] < cont:
                historial.obs(f'Navegando de regreso a la página {ultimo_caso["pagina"]}...')
                boton_primera_pagina = page.locator('body > div:nth-child(3) > div.col-sm-9 > div > div.nav-div > div > pagination-controls > pagination-template > ul > li:nth-child(3) > a')
                if boton_primera_pagina.count() > 0:
                    boton_primera_pagina.first.click()
                    time.sleep(1)
                    historial.obs('Regresado a página 1')

                pagina_actual = 1
                while pagina_actual < ultimo_caso['pagina']:
                    boton_sig = page.locator(selector_btn_sig)
                    if boton_sig.count() > 0 and boton_sig.first.is_enabled():
                        boton_sig.first.click()
                        time.sleep(1)
                        pagina_actual += 1
                        historial.info(f'Avanzando a página {pagina_actual}')
                    else:
                        break

                historial.info(f'Llegamos a la página {ultimo_caso["pagina"]}')
            # Se inicia con la descarga de la esquela
            if registro.estado_siguelo not in ['INSCRITO','REINGRESADO']:
                historial.obs('Buscando el botón de descarga...')
                boton_descarga_final = page.locator(ultimo_caso['selector'])
                boton_descarga_final.scroll_into_view_if_needed()
                time.sleep(1)

                historial.debug('Haciendo click en el botón de descarga...')
                try:
                    with page.expect_download(timeout=15000) as download_info:
                        try:
                            boton_descarga_final.click()
                        except Exception:
                            historial.debug('Click normal falló, usando JavaScript click...')
                            page.evaluate("(selector) => document.querySelector(selector).click()", ultimo_caso['selector'])
                    download_info.value.save_as(os.path.join(ruta_carpeta, nombre_archivo))
                    enviar_seguimiento(historial,registro,'descarga-documento')
                except Exception as e:
                    historial.error(f'Fallo la descarga de la esquela: {e}')
            
            # Se obtiene la fecha del estado
            valor_fecha=page.locator(ultimo_caso['selector_fecha']).inner_text()
            valor_fecha=valor_fecha.replace('FECHA :','').strip()
            fecha_estado = dt.strptime(valor_fecha, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            historial.info(f'La fecha del estado: {fecha_estado}')
            registro.fecha_estado=fecha_estado
        else:
            historial.obs('No se encontro la esquela en ninguna página')
    except Exception as e:
        historial.error(f'ERROR EN LA DESCARGA DE LA ESQUELA: {e}')
