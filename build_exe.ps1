# build.ps1 - Build completo automático para Windows (PowerShell compatible)

$script = "lu_mpd_control.py"
$qrcFile = "resources.qrc"
$resourcePy = "resources_rc.py"
$logoWebp = "logo.webp"
$iconIco = "icono.ico"

try {
    Write-Host "=== Build automático Lu MPD Controller ==="

    # 1️ Instalar dependencias
    Write-Host "Instalando dependencias..."
    python -m pip install --upgrade pip
    python -m pip install Pillow PyQt5 pyinstaller paramiko

    # 2️ Generar logo.webp y icono.ico con un script Python temporal
    $pythonLogoScript = @"
from PIL import Image, ImageDraw, ImageFont

fondo_azul = (30, 144, 255)
texto_blanco = (255, 255, 255)
tamaño = (256, 256)
img = Image.new("RGB", tamaño, fondo_azul)
draw = ImageDraw.Draw(img)
try:
    fuente = ImageFont.truetype("arialbd.ttf", size=int(tamaño[1]*0.4))
except:
    fuente = ImageFont.load_default()
texto = "MPD"
bbox = draw.textbbox((0,0), texto, font=fuente)
pos = ((tamaño[0]-(bbox[2]-bbox[0]))//2, (tamaño[1]-(bbox[3]-bbox[1]))//2)
draw.text(pos, texto, fill=texto_blanco, font=fuente)
img.save("$logoWebp", "WEBP")
# Crear icono ICO con múltiples tamaños (IMPORTANTE para Windows)
sizes = [(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)]
icon_images = []
for size in sizes:
    resized_img = img.resize(size, Image.LANCZOS)
    icon_images.append(resized_img)

# Guardar como ICO con todas las resoluciones
icon_images[0].save("$iconIco", format="ICO", sizes=sizes, append_images=icon_images[1:])
"@

    Write-Host "Generando logo e icono..."
    $pythonLogoScript | Out-File -Encoding utf8 temp_logo.py
    python temp_logo.py
    Remove-Item temp_logo.py
    Write-Host "Logo e icono generados correctamente."

    # 3️ Generar resources_rc.py desde resources.qrc
    if (Test-Path $qrcFile) {
        Write-Host "Generando $resourcePy desde $qrcFile..."
        pyrcc5 $qrcFile -o $resourcePy
        Write-Host "$resourcePy generado correctamente."
    } else {
        throw "$qrcFile no encontrado."
    }

    # 4️Limpiar builds previos
    Write-Host "Limpiando carpetas build y dist..."
    if (Test-Path ".\build") { Remove-Item -Recurse -Force ".\build" }
    if (Test-Path ".\dist") { Remove-Item -Recurse -Force ".\dist" }

    # 5️ Compilar con PyInstaller
    Write-Host "Generando exe con PyInstaller..."
    pyinstaller --onefile --windowed --icon=$iconIco $script 

    Write-Host ""
    Write-Host "Compilación finalizada correctamente."
    Write-Host "Exe generado en: .\dist\lu_mpd_control.exe"

} catch {
    Write-Host ""
    Write-Host "ERROR durante el build:"
    Write-Host $_.Exception.Message
    exit 1
}
