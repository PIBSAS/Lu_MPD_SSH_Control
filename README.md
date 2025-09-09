# Lu_MPD_SSH_Control
Control remoto MPD mediante SSH

Lo que hace es crear una app con Python y Pyinstaller para generar el `.exe` para Windows 11 con firma local, ya que su uso es para la red local donde corremos nuestro servidor MPD, como puede ser una Raspberry Pi. El porgrama realiza una conexión SSH gracias al módulo Paramiko, con Qt 5 se presenta una interfaz sencilla, que permite cargar una lista de reproducción ya realizada en MPD, y los controles básicos de reproducción, un control de volumen mediante Slider en tiempo real, asi que vas a escuchar como el audio sube o baja prograsivamente. La app queda en la barra de tareas, desde dónde tendremos un menú rápido (mediante clic derecho) para no reabrir la aplicación, también con un clic izquierdo en el icono podremos hacer `mpc toggle` es decir, Play/Pause y con doble clic abrir la ventana.


# Requirements:
- Windows 11 SDK (Windows SDK Signing Tool only)
- Python and Venv
- Clone  this repo, rename to Lu_MPD_Control.
- Create Python's Virtual Environment:
  ```python
  python -m venv .env
  ```
- Activate:
  ```python
  .env\Scripts\activate
  ```
- Edit on `crear_certificado.ps1`:
  Change for your user and set a password for the certificate.
  ```bash
  $certFolder = "C:\Users\<USER>\Lu_MPD_Control\certificados"
  $password = ConvertTo-SecureString -String "<PASSWORD>" -Force -AsPlainText
  ```
- Edit on `firmar.ps1`:
  The Correct Path to `signtool.exe`, your user, the password made it for certificate.
  ```bash
  $signtool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe"
  $exePath = "C:\Users\<YOUR USER>\Lu_MPD_Control\dist.lu_mpd_control.exe"
  $certPath = "C:\Users\<YOUR USER>\certificados\mi_certificado.pfx"
  $certPassword = "<CHOOSE A PASSWORD>"
  ```
Once all that is custom for your need, then run:
```bash
   .\build_exe.ps1
```
Then create Certificate:
```bash
   .\crear_certificado.ps1
```
Finally Sign your executable:
```bash
   .\firmar.ps1
```

Your `.exe` will be in `dist` folder. Enjoy!
