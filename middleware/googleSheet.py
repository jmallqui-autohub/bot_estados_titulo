import gspread
import os
import json
class Sheets:
    def __init__(self,):
        self.credenciales=json.loads(os.getenv('SHEET_CREDENCIALES_JOSE'))
        self.id_libro=os.getenv('SHEET_IDLIBRO')
        self.sheet=gspread.service_account_from_dict(info=self.credenciales)
        self.libro=self.sheet.open_by_key(self.id_libro)
    def abrir_hoja(self,nombre_hoja):
        self.hoja=self.libro.worksheet(nombre_hoja)
    def total_filas(self,nrocolumna):
        return len(self.hoja.col_values(nrocolumna))
    def insertar_fila(self,tuplaFila):
        self.hoja.append_row(tuplaFila)

    def obtener_columna(self,nroColumna):
        return self.hoja.col_values(nroColumna)

    def obtener_fila(self,nroFila):
        return self.hoja.row_values(nroFila)

    def obtener_valor_celda(self,nroFila,nroColumna):
        return self.hoja.cell(nroFila,nroColumna).value
    def updateCeldas(self,cell,tuplaValuesCell):
        self.hoja.update(cell,tuplaValuesCell)

    def obtener_valores_celdas(self,cells):
        return self.hoja.get(cells)

    def actualizar_celda(self,cell,tuplaValuesCell):
        self.hoja.update(cell,tuplaValuesCell)

    def obtenerTodosLosValoresListas(self):
        return self.hoja.get_all_values()

    def obtenerTodosLosValoresDiccionarios(self):
        return self.hoja.get_all_records()
    def obtener_datos(self):
        encabezados=self.hoja.row_values(1)
        filas=self.hoja.get_all_values()[1:]
        datos=[]
        for fila in filas:
            fila_dict = {}
            for i, valor in enumerate(fila):
                encabezado = encabezados[i]
                fila_dict[encabezado] = valor
            datos.append(fila_dict)
        return datos
    def obtener_nro_columna_nombre(self,encabezado):
        try:
            encabezados=self.hoja.row_values(1)
            indice = encabezados.index(encabezado)
            numero_columna=indice+1
            return numero_columna
        except ValueError:
            raise ValueError(f'El encabezado {encabezado} no existe en la hoja de calculo')
    def colorear_celda(self,celda,color):
        self.hoja.format(celda,color)

        