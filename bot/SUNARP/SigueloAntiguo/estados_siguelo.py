import os
import time
import fitz
import re
from datetime import datetime, timedelta
from PIL import Image
from playwright.sync_api import Page, BrowserContext
from utils.logger import Logger
from resources.datosfijos import RUTAPRIN,CORREOS_ERROR
from utils.funciones import transformar_b64,obtener_carpeta_descarga,extraer_text_imagen
from middleware.apis import enviar_datos_inscripcion
from middleware.funciones_correo import enviar_correo, obtener_codigo_verificacion
def ingresarPlacaYCod(page:Page,placa,codVerificacion):
	# Ingresamo la Placa
	cssInputPlaca = "body > div.swal2-container.swal2-centpageseleer.swal2-shown > div > div.swal2-content > input.swal2-input"
	page.fill(cssInputPlaca,placa)
	# Le damos al boton Siguiente
	btnSiguiente = "body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled"
	page.click(btnSiguiente)
	# Ingresamos el Codigo de Verificación
	page.fill(cssInputPlaca,codVerificacion)
def getPlaca(page:Page,fila,cssTabla):
	columaPlaca = 4
	cssCelda = getCssCelda(cssTabla,fila,columaPlaca)
	cssCeldaBoton=f"{cssCelda}>button"
	if not existeObj(page,cssCeldaBoton):
		return page.text_content(cssCelda).replace(" ","")
	return False
def nroColumnas(page:Page,cssTabla):
	nroCol = page.evaluate(('''()=>{
			return document.querySelector("%s >tbody>tr").children.length
		}''')%(cssTabla))
	return int(nroCol)

def descargaTiveYExtra(page:Page,browser:BrowserContext,cssTabla,pathDwonload,registro, historial:Logger):
	titulo=registro['titulo']
	kardex=registro['kardex']
	page.wait_for_selector(cssTabla)
	totalFilas = nroFilas(page,cssTabla)
	# descarga =1
	codigosVerificacion ={}
	errorObservacion =""
	for nroFila in range(totalFilas):
		nroFila+=1
		columaTIVE = 5
		columnaExtra = 6
		#Determinamos el nro de columnas 
		nro_columnas =nroColumnas(page,cssTabla)
		lista_columnas=[]
		if nro_columnas==5:
			lista_columnas = [columaTIVE]
		elif nro_columnas==6:
			historial.info('Hay orden de giro')
			#Comprobar si ya se descargo la orden de giro 
			lista_columnas = [columaTIVE,columnaExtra]
			#RevisionLinea
			#Se cambio debido para no descargar la orden de giro, ya que solo puede ser descargada una vez
			#lista_columnas = [columaTIVE]
		
		for nroColumna in lista_columnas:
			cssCeldai = getCssCelda(cssTabla,nroFila,nroColumna)
			cssCeldaButton = f"{cssCeldai}>button"
			
			if existeObj(page,cssCeldaButton):
				#Obtenemos placa y su respectivo codigo de verificacion
				
				placa = getPlaca(page,nroFila,cssTabla)
				
				if not placa: 
					break
				if not placa in codigosVerificacion:
					codigosVerificacion[placa] = obtener_codigo_verificacion(placa,registro,historial)
					
				codVerificacion =  codigosVerificacion[placa]
				registro['codigoVer'] = codVerificacion
				registro['placa'] = placa
				if not codVerificacion:
					errorObservacion = "Descarga incompleta, no se encontro código de verificación."
					return errorObservacion
				page.click(cssCeldaButton)
				ingresarPlacaYCod(page,placa,codVerificacion)
				nameFile = "TIVE" if nroColumna == 5 else  "EXTRA"
				pathTempDwonload = os.path.join(pathDwonload,f'{kardex}-{titulo}_{nameFile}_{nroFila}.pdf')
				btnSiguienteDwonload = "body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled"
				if nroColumna ==6:
					#Comprobar que orden de giro ya ha sido descargada anteriormente y esta en el sistema local
					################
					if os.path.exists(pathTempDwonload):
						historial.obs("Archivo de Orden de giro ya existe en esta computadora")
						errorObservacion = ""
					###############
					else:
						historial.info('Descargando Orden de Giro')
						page.click(btnSiguienteDwonload)
						btnSiguienteDwonload ="body > div.swal2-container.swal2-center.swal2-shown > div > div.swal2-actions > button.swal2-confirm.swal2-styled"
						observacion=descargar_esquela_siguelo(btnSiguienteDwonload,pathTempDwonload)
						if not observacion:
							mensaje=f'--> Se descargo: {pathDwonload}'
							historial.info(mensaje)
							if len(browser.pages)>1:
								browser.pages[1].close()
							errorObservacion=''
						else:
							mensaje=f"--> Observación: {observacion}"
							historial.obs(mensaje)
							page.keyboard.press("Escape")
							page.keyboard.press("Escape")
							errorObservacion=observacion
					if errorObservacion:
						return errorObservacion
				else:
					observacion=descargar_esquela_siguelo(btnSiguienteDwonload,pathTempDwonload)
					if not observacion:
						mensaje=f'--> Se descargo: {pathDwonload}'
						historial.info(mensaje)
						if len(browser.pages)>1:
							browser.pages[1].close()
						errorObservacion=''
					else:
						mensaje=f"--> Observación: {observacion}"
						historial.obs(mensaje)
						page.keyboard.press("Escape")
						page.keyboard.press("Escape")
					if errorObservacion:
						return errorObservacion
			else:
				errorObservacion="Se encontro celda vacia de descarga('Tive o extra') en cuadro de asientos."
	
	return errorObservacion
def descargasEnTabla(page:Page, browser:BrowserContext,cssTabla,nroColumna,pathDwonload,registro,historial:Logger):
	titulo=registro['titulo']
	kardex=registro['kardex']
	page.wait_for_selector(cssTabla,timeout=60000)
	totalDocs = nroFilas(page,cssTabla)
	descarga =1
	errorObservacion =""
	nroFila=0
	# Se recorre todas la filas con el contador "nroFila"
	while nroFila < totalDocs:
		nroFila +=1
		cssFila = getCssCelda(cssTabla,nroFila,nroColumna)
		cssFilaButton = f"{cssFila}>button"
		pathTempDwonload = os.path.join(pathDwonload,f'{kardex}-{titulo}_ASIENTO_{descarga}.pdf')
		observacion=descargar_esquela_siguelo(cssFilaButton,pathTempDwonload)
		if not observacion:
			mensaje=f'--> Se descargo: {pathDwonload}'
			historial.info(mensaje)
			if len(browser.pages)>1:
				browser.pages[1].close()
			errorObservacion=''
		else:
			mensaje=f"--> Observación: {observacion}"
			historial.obs(mensaje)
			page.keyboard.press("Escape")
			page.keyboard.press("Escape")
			errorObservacion=observacion
		if errorObservacion=='Le quedan  2 Minutos  para finalizar su Consulta':
			return errorObservacion
		else:
			descarga+=1
	return errorObservacion
def protocoloAsientosVehicular(page:Page,browser:BrowserContext,kardex,titulo,historial:Logger,registro):
	#Parche para casos de encuesta
	cuadroEncuesta = "body > div.cdk-overlay-container > div.cdk-global-overlay-wrapper > div:nth-child(1)"
	ExisteEncuesta = page.evaluate(('''()=>{
			var doc = document.querySelector('%s');
			return doc
		}''')%(cuadroEncuesta))
	if ExisteEncuesta!=None:
		print('se encontro encuesta')
		time.sleep(4)
		page.keyboard.press('Enter')
		page.wait_for_selector('body > div.cdk-overlay-container > div.cdk-global-overlay-wrapper > div:nth-child(1) > mat-dialog-container > app-encuesta > mat-card-header > mat-toolbar > mat-icon',timeout=90000)
		page.click('body > div.cdk-overlay-container > div.cdk-global-overlay-wrapper > div:nth-child(1) > mat-dialog-container > app-encuesta > mat-card-header > mat-toolbar > mat-icon')
	cssSecAsientos ="body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(4) > td > a"
	
	page.click(cssSecAsientos) #Click a boton "Ver asientos de inscripcion"
	#Tabla de popup que aparece al dar click a Ver asientos
	cssTabla ="body > div.cdk-overlay-container > div.cdk-global-overlay-wrapper > div:nth-child(1) > mat-dialog-container> app-partidas > mat-card-content > div > div > table"
	page.wait_for_selector(cssTabla,timeout=90000)

	pathDwonload = obtener_carpeta_descarga(kardex,titulo) 	
	nroColumnaAsiento = 3
	pathDwonloadAsiento = f"{pathDwonload}_ASIENTO"
	# Se busca errores de Observacion en las busqueda de tablas, Tives y extras
	
	errorObservacion = descargasEnTabla(page,browser,cssTabla,nroColumnaAsiento,pathDwonload, registro,historial)
	errorObservacion = descargaTiveYExtra(page,browser,cssTabla,pathDwonload,registro,historial)
	if errorObservacion.find("No se encontró coincidencia, por favor verifique que los datos ingresados son correctos.")!=-1:
		return ""
	return errorObservacion
def TryDescargarAsientos(page:Page,browser:BrowserContext,registro,historial:Logger):
	try:
		errores=""
		titulo = registro["titulo"] 
		kardex=registro['kardex']
		errores = protocoloAsientosVehicular(page,browser,kardex,titulo,historial,registro)
		# Si existe algun error se realizara una observación
		if errores=="Descarga incompleta, no se encontro código de verificación.":
			registro["estado"] = "INCOMPLETO"
			historial.error(errores)
			return False
		elif errores:
			if not errores=="Se encontro celda vacia de descarga('Tive o extra') en cuadro de asientos.":
				registro["estado"] = "INCOMPLETO"
			registro["observacion"] =f"Error al descargar asientos {errores}"
			historial.error(registro['observacion'])
			return False
		return True
	except Exception as inst:
		mensaje=f'Error al descargar los asientos. {inst}'
		historial.debug(mensaje)
		historial.error("======|||| ERROR INESPERADO |||======")
		registro["observacion"] =f"No hay asientos de inscripción en Siguelo."
		registro["estado"] = "INCOMPLETO"
		return False
def TryDescargarAnotacion(page:Page, browser:BrowserContext,registro,historial:Logger):
	try:
		titulo =registro["titulo"]
		kardex=registro['kardex']
		cssBotonAnotacion ="body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(5) > td > a > span" 
		ruta_carpeta = obtener_carpeta_descarga(kardex,titulo)
		pathDwonload = f"{pathDwonload}_anotacion.pdf"
		pathDwonload = os.path.join(ruta_carpeta,f'{kardex}-{titulo}_anotacion.pdf')
		observacion=descargar_esquela_siguelo(cssBotonAnotacion,pathDwonload)
		if not observacion:
			mensaje=f'--> Se descargo: {pathDwonload}'
			historial.info(mensaje)
			if len(browser.pages)>1:
				browser.pages[1].close()
			errorObservacion=''
		else:
			mensaje=f"--> Observación: {observacion}"
			historial.obs(mensaje)
			page.keyboard.press("Escape")
			page.keyboard.press("Escape")
			errorObservacion=observacion

		if errorObservacion:
			registro["observacion"] =f"No hay archivo de anotación en la página de Siguelo. Mensaje:{errorObservacion}"
			registro["estado"] = "INCOMPLETO"
			historial.error(registro['observacion'])
			return False
		return True

	except Exception as inst:
		mensaje=f'Error inesperado al descargar anotación. {inst}'
		registro["observacion"] =f"Error inesperado al descargar anotación."
		registro["estado"] = "INCOMPLETO"
		historial.error(mensaje)
		return False
def extraer_monto_pagar(ruta):
	documento=fitz.open(ruta)
	texto=''
	for pagina in range(documento.page_count):
		hoja=documento[pagina]
		rotate=int(0)
		# el factor de escala para cada tamaño es 3, lo que generara una imagen con cuatro veces la resolucion para nosotros
		zoom_x=2.0
		zoom_y=2.0
		trans=fitz.Matrix(zoom_x,zoom_y).prerotate(rotate)
		pm=hoja.get_pixmap(matrix=trans,alpha=False)
		img=Image.frombytes("RGB",[pm.width,pm.heigth],pm.samples)
		texto=texto+extraer_text_imagen(img)
	try:
		frase1=re.search(r'Derechos por Pagar S/.',texto)
		frase2=re.search(r'Diferencia por Pagar',texto)
		frase3=re.search(r'Derechos por Pagar',texto)
		if frase1:
			frase=re.search(r'Derechos por Pagar S/.',texto).end()
		elif frase2:
			frase=re.search(r'Derechos por Pagar S/.',texto).end()
		elif frase3:
			frase=re.search(r'Derechos por Pagar S/.',texto).end()
		else:
			return False
		x=0
		while not texto[frase+x].isdigit():
			x+=1
		frase=frase+x
		y=0
		while (texto[frase+y].isdigit() or texto[frase+y]==',' or texto[frase+y]=='' or texto[frase+y]=='.') and frase+y<=len(texto):
			monto=texto[frase:frase+y+1]
			y+=1
		monto = monto.replace(',','').replace("'","")
		monto=int(monto)
		return monto
	except:
		return False   
def TryGetMontoLiquidacion(registro,historial:Logger):
	try:
		titulo = registro["titulo"]
		kardex=registro['kardex']
		pathPdfLiquidacion = os.path.join(RUTAPRIN,'download',f'{kardex}-{titulo}',f'{kardex}-{titulo}_ESQUELA DE LIQUIDACIÓN_1.pdf')
		monto = extraer_monto_pagar(pathPdfLiquidacion)
		if monto:
			registro["montoDevolver"] = monto
			mensaje=f"Monto por liquidacion: {monto}"
			historial.info(mensaje)
			return True
		else:
			mensaje='No se encontró el monto en el documento PDF.'
			registro["observacion"] =mensaje
			historial.error(mensaje)
			registro["estado"] = "INCOMPLETO"
			return False
	except Exception as inst:
		mensaje=f'No se encontró el documento en la página de SUNARP. (Síguelo).{inst}'
		registro["observacion"] ="No se encontró el documento en la página de SUNARP. (Síguelo)"
		historial.error(mensaje)
		registro["estado"] = "INCOMPLETO"
		return False
def TryGetFechaVenc(page:Page,registro,historial:Logger):
	try:
		page.wait_for_selector('#fechaVencimiento')
		f_vencimiento = page.evaluate("()=>{return document.querySelector('#fechaVencimiento').value;}")
		if len(f_vencimiento)>14:
			f_vencimiento = datetime.strptime(f_vencimiento, '%Y-%m-%d %H:%M:%S.%f')
		else:
			f_vencimiento = datetime.strptime(f_vencimiento, '%d/%m/%Y')
		mensaje=f'Fechas de venvimiento: {f_vencimiento}'
		historial.info(mensaje)
		new_f_vencimiento = f_vencimiento - timedelta(days=7)
		new_f_vencimiento = str(new_f_vencimiento)
		recorte = new_f_vencimiento[0:10]
		partes = recorte.split("T")[0].split("-")
		f_vencimiento2 = "/".join(reversed(partes))
		historial.info(f_vencimiento2)
		registro["fVencimiento"] = f_vencimiento2
		return True
	except Exception as inst:
		mensaje=f"Error al leer fecha de vencimiento de titulo. {inst}"
		registro["observacion"] ="Error al leer fecha de vencimiento de titulo."
		historial.error(mensaje)
		registro["estado"] = "INCOMPLETO"
		return False
def aparece_aviso(page:Page,cssAviso):
    existe_aviso = page.evaluate(('''()=>{
            if (document.querySelector("%s")){
                return true
            }
            else{
                return false
            }
    }''')%(cssAviso))
    return existe_aviso
def descargar_esquela_siguelo( page:Page,cssFilaBoton,ruta):
    veces=0
    page.wait_for_selector(cssFilaBoton)
    while veces<10:
        veces+=1
        try:
            with page.expect_download(timeout=20000) as download_info:
                page.click(cssFilaBoton)
            download = download_info.value
            download.save_as(ruta)
            return False
        except:
            pass
        cssAviso = "#swal2-content > table > tbody > tr > td > p"
        if aparece_aviso(page,cssAviso):
            return page.text_content(cssAviso)
        cssAviso = "body > div.swal-overlay.swal-overlay--show-modal > div > div.swal-text"
        if aparece_aviso(page,cssAviso):
            return page.text_content(cssAviso)
    return "Error descarga inesperado"
		
def waitRefreshTable(page:Page,cssTabla,primeraFila):
	cssCelda1 =f"{cssTabla} tbody > tr > td"
	nroFila=""
	while not nroFila == primeraFila:
		nroFila = page.text_content(cssCelda1)
		nroFila = int(nroFila)
def existeObj(page:Page,selectorObjeto):
    existeObj = page.evaluate(('''()=>{ 
                if (document.querySelector("%s")){
                    return true;
                }
                else{
                    return false;
                } 
                }''')%(selectorObjeto))
    return existeObj
def getCssCelda(cssTabla,fila,columna):
	return f"{cssTabla}>tbody>tr:nth-child({fila})>td:nth-child({columna})"
def nroFilas(page:Page,cssTabla):
	nroFilas = page.evaluate(('''()=>{
			return document.querySelector("%s > tbody").children.length
		}''')%(cssTabla))
	return int(nroFilas)
def TryGetMontoDevolver(page:Page,registro,historial:Logger):	
	try:
		time.sleep(1)
		monto_devolver = page.evaluate('''()=>{
			monto = document.querySelector("body > div:nth-child(10) > div.col-sm-1 > div > span").textContent;
			monto=parseFloat(monto.replace(/[S/,]/g, ""));
			return monto;
		}''')
		registro["montoDevolver"] = monto_devolver
		#ACA SE PONDRIA LA FUNCION PARA PODER INSERTAR EL MONTOXDEVOLVER EN EL SHEETS
		if int(monto_devolver) !=0:
			print("Funcion insertar monto por devolver comentadaa... ")
   			#insertMontoxDevolver(kardex,jsonKardex)
		#anexar_historial(pathtexto, f"Monto devolver: {monto_devolver}")
		return True
	except Exception as inst:
		mensaje=f"Error al leer monto a devolver: {inst}"
		historial.error(mensaje)
		registro["observacion"] ="Error al leer el monto a devolver en Siguelo."
		registro["estado"] = "INCOMPLETO"
		return False
def descargarContarEsquelas(page:Page,browser:BrowserContext,nombreEsquela,kardex,titulo,historial:Logger):
	#Ingresa a sección "Detalle de seguimiento"
	page.click('body > div:nth-child(14) > div:nth-child(3) > table > tr:nth-child(1) > td > a > span')
	paginaActual = 1
	nroDescarga  = 0
	totalFilas   = 0
	cssTabla="#gridDiv> table"
	pathDwonload = obtener_carpeta_descarga(kardex,titulo)
	errorObservacion =""
	while True:
		# print('hace un ciclo en el while')
		page.wait_for_selector(cssTabla)
		totalFilasTemp = nroFilas(page,cssTabla)
		for nroFila in range(totalFilasTemp):
			nroFila +=1
			cssCelda = getCssCelda(cssTabla,nroFila,5)
			# cssCelda tiene un icono entonces text_content es 'local_atm Ver Pago'
			textoBoton = page.text_content(cssCelda)
			# Path para descargar la Esquela
			#pathDwonloadTemp = f"{pathDwonload}_{nombreEsquela}_{nroDescarga}.pdf"
			if nombreEsquela in textoBoton.upper():
				cssFilaButton = f"{cssCelda}>div>a" #Etiqueta con link >div>a
				paginaDeEsquela=paginaActual
				#errorObservacion += siguelo.descargar(cssFilaButton,pathDwonloadTemp)
				#if not errorObservacion:
					#nroDescarga+=1
				# print('Se aumentara en 1 el nroDescarga')
				nroDescarga+=1
		#Seguimos a la siguiente tabla si existe
		selectorBtnNext = "body>div:nth-child(3)>div.col-sm-9>div>div.nav-div>div>pagination-controls>pagination-template>ul>li.pagination-next.ng-star-inserted>a"
		if existeObj(page,selectorBtnNext):
			paginaActual = paginaActual+1
			totalFilas +=totalFilasTemp
			page.click(selectorBtnNext)
			waitRefreshTable(page,cssTabla,totalFilas+1)
		else:
			while paginaDeEsquela != paginaActual:
				page.click("body > div:nth-child(3) > div.col-sm-9 > div > div.nav-div > div > pagination-controls > pagination-template > ul > li.pagination-previous.ng-star-inserted > a")
				paginaActual = paginaActual-1
			print('El nro de descarga es: ',nroDescarga)
			pathDwonloadTemp = os.path.join(pathDwonload,f'{kardex}-{titulo}_{nombreEsquela}_{nroDescarga}.pdf')
			observacion=descargar_esquela_siguelo(cssFilaButton,pathDwonloadTemp)
			if not observacion:
				mensaje=f'--> Se descargo: {pathDwonloadTemp}'
				historial.info(mensaje)
				if len(browser.pages)>1:
					browser.pages[1].close()
				errorObservacion=''
			else:
				mensaje=f"--> Observación: {observacion}"
				historial.obs(mensaje)
				page.keyboard.press("Escape")
				page.keyboard.press("Escape")
				errorObservacion=observacion
			break
	# Salimos de la sección de esquelas
 # Click en boton salir 
	page.click("#navbarSupportedContent > ul > li:nth-child(1) > a")
	return errorObservacion

def TryDescargarEsquelas(page:Page,browser:BrowserContext,registro,nameFile,historial:Logger):
	try:
		titulo = registro["titulo"]
		kardex=registro['kardex']
		errores = descargarContarEsquelas(page,browser,nameFile,kardex,titulo)
		if errores:
			if errores==" Se produjo un inconveniente, intentelo en unos momentos por favor. ":
				registro["observacion"] ="No se encontró el documento en la página de SUNARP. (Síguelo)"
				registro["estado"] = "INCOMPLETO"
				historial.error(registro['observacion'])
			else:
				registro["observacion"] =f"Error al descargar esquelas. {errores}."
				registro["estado"] = "INCOMPLETO"
				historial.error(registro['observacion'])
			return False
		else: return True
	except Exception as inst:
		fecha_hoy=datetime.now().strftime("%d-%m-%Y")
		ruta=os.path.join(RUTAPRIN,'download','capturasErrorSiguelo',f'captura_{fecha_hoy}.png')
		page.screenshot(path=ruta)
		registro["observacion"] =f"Error inesperado al descargar esquelas."
		registro["estado"] = "INCOMPLETO"
		mensaje=f'Error inesperado al descargar esquelas.{inst}'
		historial.error(mensaje)
		return False

def tryGetEstadoTitulo(page:Page,registro,historial:Logger):
	try:
		estado_titulo = page.text_content("body > div:nth-child(11) > div.col-sm-6 > div > div:nth-child(1)").strip().upper()
		registro["estadotitulo"] = estado_titulo
		return estado_titulo
	except:
		historial.error("Error al leer estado de titulo")
		registro["observacion"] ="Error al leer estado de titulo."
		registro["estado"] = "INCOMPLETO"
		return False
def protocoloSegunEstado(page:Page, browser:BrowserContext,registro,historial:Logger,estadosiguelo,valorEnvio):

	try:		
		page.wait_for_selector("#iconoSunarp")
	except:
		mensaje="Tiempo de espera agotada para carga de pagina de siguelo."
		registro["observacion"] =mensaje
		historial.obs(mensaje)
		return False

	# Se intenta obtener el Estado del Titulo de la pagina Siguelo
	estadoTitulo = tryGetEstadoTitulo(page,registro,historial)
	if estadoTitulo ==estadosiguelo and registro["estado"] != "INCOMPLETO":
		print("No hubo cambios del estado en el siguelo")
		mensaje=f"Estado del titulo: {estadoTitulo}- No hubo cambios del estado en el siguelo"
		historial.obs(mensaje)
		return valorEnvio	
	else:
		if estadoTitulo and estadoTitulo in ['APELADO','EN CALIFICACIÓN','EN PROCESO',"PRESENTADO","REINGRESADO","DISTRIBUIDO","PRORROGADO","RESERVADO","EN CALIFICACION"]:
			# El estado más común, - Estado sin acciones
			mensaje=f"---> Estado titulo: {estadoTitulo} - Estado sin acciones."
			historial.obs(mensaje)
			registro["estado"] ="PENDIENTE"
			return valorEnvio
		#Estados finales 
		#--------------------------------------- ESTADO TACHADO---------------------------------------	
		elif estadoTitulo == 'TACHADO':
			mensaje=f"---> Estado titulo: {estadoTitulo}"
			historial.info(mensaje)
			# Funcion que intenta obtener el monto Devolver y Descargar Esquelas
			if not TryGetMontoDevolver(page,registro,historial) : return valorEnvio
			if not TryDescargarEsquelas(page,browser,registro,"ESQUELA DE TACHA",historial) : return valorEnvio
			registro["estado"]="OPENCLOUD"
			return valorEnvio
		#--------------------------------------- ESTADO OBSERVADO---------------------------------------	
		elif estadoTitulo == 'OBSERVADO':
			mensaje=f"---> Estado titulo: {estadoTitulo}"
			historial.info(mensaje)
			# Función que intenta la obtención de Fecha de vencimiento de OBSERVADO
			if not TryGetFechaVenc(page,registro,historial): return valorEnvio
			if not TryDescargarEsquelas(page,browser,registro,"ESQUELA DE OBSERVACIÓN",historial) : return valorEnvio
			registro["estado"]="OPENCLOUD"
			valorEnvio=1
			return valorEnvio
		#--------------------------------------- ESTADO SUSPENDIDO---------------------------------------	
		elif estadoTitulo=='SUSPENDIDO':
			if estadosiguelo=='OBSERVADO':
				registro["estado"]="SUSPENDIDO"
				return valorEnvio
			else:
				mensaje=f"---> Estado titulo: {estadoTitulo}"
				historial.info(mensaje)
				# Función que intenta la obtención de Fecha de vencimiento de OBSERVADO
				if not TryGetFechaVenc(page, registro,historial): return valorEnvio
				if not TryDescargarEsquelas(page,browser,registro,"ESQUELA DE OBSERVACIÓN",historial) : return valorEnvio
				registro["estado"]="OPENCLOUD"
				valorEnvio=1
			return valorEnvio
		#--------------------------------------- ESTADO LIQUIDADO---------------------------------------	
		elif estadoTitulo == 'LIQUIDADO':
			mensaje=f"---> Estado titulo: {estadoTitulo}"
			historial.info(mensaje)
			# Función que intenta la obtención de Fecha de vencimiento de LIQUIDADO
			if not TryGetFechaVenc(page,registro,historial) : return valorEnvio
			if not TryDescargarEsquelas(page,browser,registro,"ESQUELA DE LIQUIDACIÓN",historial) : return valorEnvio
			if not TryGetMontoLiquidacion(registro, historial): return valorEnvio
			registro["estado"]="OPENCLOUD"
			valorEnvio=1
			return valorEnvio
		#--------------------------------------- ESTADO INSCRITO---------------------------------------	
		elif estadoTitulo == 'INSCRITO':
			mensaje=f"---> Estado titulo: {estadoTitulo}"
			historial.info(mensaje)
			# Se intenta obetener el Monto Devolver, Descargar Anotacion y Descarga Asientos
			if not TryGetMontoDevolver(page,registro,historial) : return valorEnvio
			if not TryDescargarAnotacion(page,browser,registro,historial): return valorEnvio
			if not TryDescargarAsientos(page, browser, registro, historial): return valorEnvio
			nombre_carpeta=f'{registro['kardex']}-{registro['titulo']}'
			ruta_tive=os.path.join(RUTAPRIN,'download',nombre_carpeta,f'{nombre_carpeta}_TIVE_1.pdf')
			ruta_insc=os.path.join(RUTAPRIN,'download',nombre_carpeta,f'{nombre_carpeta}_ASIENTO_1.pdf')
			ruta_orden=os.path.join(RUTAPRIN,'download',nombre_carpeta,f'{nombre_carpeta}_EXTRA_1.pdf')
			nombreTive=os.path.basename(ruta_tive)
			nombreInscripcion=os.path.basename(ruta_insc)
			nombreOrdenGiro=os.path.basename(ruta_orden)
			file_tive_64=transformar_b64(ruta_tive)
			file_insc_64=transformar_b64(ruta_insc)
			file_ordeng_64=transformar_b64(ruta_orden)
			codigoVerificacion=registro["codigoVer"]
			placa_kardex=registro["placa"]
			inmatriculacion=registro["inmatriculacion"]
			body={
				"kardex":registro['kardex'],
				"file":file_tive_64,
				"filename":nombreTive,
				"codigo_verificacion":codigoVerificacion,
				"placa":placa_kardex,
				"inmatriculacion":inmatriculacion,
				"file2":file_insc_64,
				"filename2":nombreInscripcion,
				"file3":file_ordeng_64,
				"filename3":nombreOrdenGiro
			}
			res=enviar_datos_inscripcion(body)
			if res==200:
				mensaje="Se envio correctamente los datos a la api"
				historial.info(mensaje)
			else:
				subject=f"Bot3 Inmatriculaciones-Error inscripcion - Nro Inmatriculacion {inmatriculacion} "
				mensaje=f"Ocurrio el siguiente error al realizar la consulta de la Api para la inmatriculacion {inmatriculacion} del kardex {registro['kardex']} : {res}" 
				enviar_correo(CORREOS_ERROR,subject,mensaje,1,'','',False,historial)
				registro["estado"]="INCOMPLETO"
				return valorEnvio
			registro["estado"]="OPENCLOUD"
			registro["estadobot4"]="PENDIENTE"
			return valorEnvio