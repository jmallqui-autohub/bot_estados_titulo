from dataclasses import dataclass

@dataclass
class Inmatriculacion:
    interno :str =''
    bot:str=''
    id:int=0
    kardex: str | None =None
    titulo: str =''
    placa: str =''
    oficina: str =''
    anio: str =''
    compania: str =''
    observacion:str =''
    estado_siguelo: str =''
    estado_autohub: str =''
    estado: str =''
    titulo_tipo: str =''
    codigo_verificacion: str =''
    fecha_vencimiento: str | None = None
    monto_devolver:str | None = None
    fecha_presentacion: str =''
    fecha_estado: str =''
    tramite:str =''
    inicio_sesion: int=0
    orden_giro:bool=True



