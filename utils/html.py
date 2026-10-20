from resources.datosfijos import *
from resources.inmatriculacion import Inmatriculacion
def generar_html_autohub(tipo,inmatriculacion,kardex,titulo,anio):
    html_content = f"""
    <html>
        <body>
            <div>
                <div style="border: 1px solid #003366;padding: 10px;width: 90%;margin: 0;">
                    <div style="background:linear-gradient(to right, #003366, #000D1A); text-align:center; text-justify:center; padding-top:20px; padding-bottom:20px" >
                        <h1 style="color:#FFFFFF;font-family:Google Sans; font-size: 24px; margin: 0; ">
                                                AUTOHUB</h1>
                    </div>
                    <div style="padding: 10px">
                        <p style="font-family:Google Sans; font-size: 16px;"> Por medio de la presente, se informa que Sunarp  {tipo} la siguiente inmatriculación:</p>
                        <table style="padding-left:20px">
                            <tbody>
                                <tr>
                                    <td style="font-family:Google Sans; font-size: 15px;">Nro. Inmatriculación: {inmatriculacion}</td>
                                </tr>
                                <tr>
                                    <td style="font-family:Google Sans; font-size: 15px;">Nro. Kardex Asociado: {kardex}</td>
                                </tr>
                                <tr>
                                    <td style="font-family:Google Sans; font-size: 15px;">Nro. Título: {titulo}</td>
                                </tr>
                                <tr>
                                    <td style="font-family:Google Sans; font-size: 15px;">Nro. Año: {anio}</td>
                                </tr>
                            </tbody>
                        </table>
                        <p style="font-family:Google Sans; font-size: 16px;"> 
                            <strong>En breves momentos la notaría responderá con lo necesario para la subsanación de la observación.</strong>
                        </p>
                    </div>
                </div>
            </div>    
        </body>
    </html>
    """
    return html_content

def generar_html_reclamos(fecha_presentacion,titulo,anio,oficina):
    html_content = f"""
    <html>
        <body>
            <div>
                    <div style="padding: 10px">
                        <p style="font-family:Google Sans; font-size: 16px;">Estimados señores de la Defensoría:</p>
                        <p style="font-family:Google Sans; font-size: 16px;">Por medio de la presente, solicito su apoyo para realizar el reclamo del Título N.º <strong> {titulo}-{anio} </strong>, presentado el <strong>{fecha_presentacion}</strong> ante el Registro Vehicular de {str(oficina).capitalize()}.</p>
                        <p style="font-family:Google Sans; font-size: 16px;">Hasta la fecha, no hemos recibido pronunciamiento por parte del registrador, por lo que agradeceré su gentil intervención y pronta respuesta al respecto.</p>
                        <p style="font-family:Google Sans; font-size: 16px;">Atentamente,</p>
                        <p style="font-family:Google Sans; font-size: 16px;">Lilliam Huallullo</p>
                    </div>

            </div>    
        </body>
    </html>
    """
    return html_content

def generar_html_errores_siguelo(imagen_b64,registro:Inmatriculacion):
    html_content = f"""
    <html>
        <body>
            <div style="font-family: Arial, sans-serif; padding: 10px;">
                <h3>No se pudo descargar del siguelo: </h3>
                <p><b>Inmatriculación:</b> {registro.interno}</p>
                <p><b>Título:</b> {registro.titulo} - {registro.anio}</p>
                <p><b>Compañía:</b> {COMPANIAS.get(registro.compania, 'NUEVA COMPANIA')}</p>
                <p><b>Motivo:</b> {registro.observacion}</p>
            </div>
            <img src="data:image/png;base64,{imagen_b64}" alt="Captura error" style="border: 2px solid #ccc; max-width: 100%;">
        </body>
    </html>
    """
    return html_content

