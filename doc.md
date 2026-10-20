3. Instalar KVM y herramientas de virtualización

Instala el hipervisor KVM, QEMU y las herramientas de gestión de red y almacenamiento:
Bash

sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils -y

4. Instalar Virt-Manager

Ahora instala la interfaz gráfica:
Bash

sudo apt install virt-manager -y

5. Iniciar y habilitar el servicio de virtualización

Asegúrate de que el servicio libvirtd esté activo y configurado para iniciar con el sistema:
Bash

sudo systemctl enable --now libvirtd

6. Agregar tu usuario a los permisos necesarios

Para poder administrar máquinas virtuales sin necesidad de usar sudo todo el tiempo, añade tu usuario a los grupos libvirt y kvm:
Bash

sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER


--------------------------------------------------------------------------------

 convertir el archivo de mi maquina virtual vmdk a formato de archivo compatible con virtmanager para crear mi maquina virtual en base a este archivo 

Paso 1: Instalar la herramienta de conversión  

Si aún no la tienes, necesitas la utilidad qemu-img:  

Bash

sudo apt install qemu-utils -y

Paso 2: Convertir el archivo VMDK a QCOW2

Abre tu terminal, dirígete a la carpeta donde tienes tu archivo .vmdk y ejecuta el siguiente comando:
Bash

qemu-img convert -f vmdk -O qcow2 archivo_original.vmdk archivo_convertido.qcow2

    -f vmdk: Especifica el formato del archivo de entrada.

    -O qcow2: Especifica el formato de salida compatible con KVM.

    (Opcional) Puedes agregar la bandera -p entre convert y -f si deseas ver una barra de progreso durante la conversión.

    Nota importante: Asegúrate de tener suficiente espacio libre en disco en la ruta de destino, ya que el proceso descomprimirá o generará la imagen completa equivalente.  

Paso 3: Crear la máquina virtual en Virt-Manager usando el nuevo archivo

Una vez finalizada la conversión (archivo_convertido.qcow2), puedes agregarlo fácilmente a Virt-Manager:

    Abre Virt-Manager ("Gestor de máquinas virtuales").

    Haz clic en el botón de la esquina superior izquierda para crear una nueva máquina virtual (Create a new virtual machine).

    Selecciona la opción Import existing disk image (Importar imagen de disco existente) y haz clic en Forward.

    Haz clic en Browse (Examinar) y luego en Browse Local (Examinar localmente) para buscar y seleccionar tu archivo recién convertido archivo_convertido.qcow2.

    Selecciona el sistema operativo invitado (OS) correspondiente y haz clic en Forward.

    Define la cantidad de memoria RAM y núcleos de CPU que tendrá la máquina virtual.

    Dale un nombre a tu máquina virtual, verifica las opciones de red y haz clic en Finish.
