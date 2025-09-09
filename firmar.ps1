$signtool = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe"
$exePath = "C:\Users\<YOUR USER>\Lu_MPD_Control\dist.lu_mpd_control.exe"
$certPath = "C:\Users\<YOUR USER>\certificados\mi_certificado.pfx"
$certPassword = "<CHOOSE A PASSWORD>"

Write-Host "Firmando $exePath con $certPath..."

& $signtool sign /f $certPath /p $certPassword /tr http://timestamp.digicert.com /td sha256 /fd sha256 $exePath

Write-Host "EXE firmado. Listo para usar."
