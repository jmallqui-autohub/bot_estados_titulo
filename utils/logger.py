import logging
from datetime import datetime
from pathlib import Path
from colorama import init, Fore

init(autoreset=True)

class Logger:
    def __init__(self,bot):
        """Inicializa el logger con logs diarios guardados en la carpeta /logs del proyecto"""

        # Ruta a la raíz del proyecto (2 niveles arriba del archivo actual)
        raiz_proyecto = Path(__file__).resolve().parent.parent
        carpeta_log = raiz_proyecto / "logs"
        carpeta_log.mkdir(parents=True, exist_ok=True)  # Crea la carpeta si no existe

        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo = carpeta_log / f"BOT {bot} ({fecha_hoy}).log"

        # Crear el logger
        self.logger = logging.getLogger("LoggerGlobal")
        self.logger.setLevel(logging.DEBUG)

        # Formato para el archivo de log (con hora)
        class CustomFormatter(logging.Formatter):
            def format(self, record):
                if record.levelname == "WARNING":
                    record.levelname = "OBS"
                if record.levelname == "CRITICAL":
                    record.levelname="TITLE"
                nivel_max_len = 11  # Longitud máxima del nivel
                nivel_formateado = record.levelname.ljust(nivel_max_len)
                
                hora_actual = datetime.now().strftime("%H:%M:%S")  # Solo hora
                lineas = record.msg.split("\n")
                primera_linea = f"{nivel_formateado} - {lineas[0]} - {hora_actual}"
                espacios = " " * len(nivel_formateado + " - ")
                lineas_extra = "\n".join(f"{espacios}{linea}" for linea in lineas[1:])

                return primera_linea + ("\n" + lineas_extra if lineas_extra else "")

        formato = CustomFormatter("%(message)s")

        manejador_archivo = logging.FileHandler(str(nombre_archivo), mode="a", encoding="utf-8")
        manejador_archivo.setFormatter(formato)
        self.logger.addHandler(manejador_archivo)

    class ColoredFormatter:
        """Clase para imprimir logs en consola con color y sin la hora"""
        COLORS = {
            "DEBUG": Fore.CYAN,
            "INFO": Fore.GREEN,
            "OBS": Fore.YELLOW,
            "ERROR": Fore.RED,
            "CRITICAL": Fore.MAGENTA,
            "TITLE":Fore.LIGHTBLUE_EX
        }

        @staticmethod
        def format(level, message):
            nivel_max_len = 11
            if level.upper()== "WARNING":
                display_level = "OBS"
            elif level.upper() == "CRITICAL":
                display_level="TITLE"
            else: display_level=level.upper()
            nivel_formateado = display_level.ljust(nivel_max_len)

            lineas = message.split("\n")
            primera_linea = f"{nivel_formateado} - {lineas[0]}"
            espacios = " " * len(nivel_formateado + " - ")
            lineas_extra = "\n".join(f"{espacios}{linea}" for linea in lineas[1:])
            mensaje_alineado = primera_linea + ("\n" + lineas_extra if lineas_extra else "")

            color = Logger.ColoredFormatter.COLORS.get(display_level, Fore.WHITE)
            return f"{color}{mensaje_alineado}"

    def _log(self, level, message, condicion=False):
        """Método interno para manejar los logs"""
        getattr(self.logger, level.lower())(message)

        if condicion:
            print(self.ColoredFormatter.format(level, message))

    def debug(self, mensaje, condicion=False):
        self._log("DEBUG", mensaje, condicion)

    def info(self, mensaje, condicion=True):
        self._log("INFO", mensaje, condicion)

    def obs(self, mensaje, condicion=True):
        self._log("WARNING", mensaje, condicion)

    def error(self, mensaje, condicion=True):
        self._log("ERROR", mensaje, condicion)

    def critical(self, mensaje, condicion=False):
        self._log("CRITICAL", mensaje, condicion)

    def title(self,mensaje,condicion=True):
        self._log('CRITICAL',mensaje,condicion)