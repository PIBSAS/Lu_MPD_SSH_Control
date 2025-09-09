# --- Variables ---
$certName = "Lu MPD Controller Test Certificate"
$certFolder = "C:\Users\<USER>\Lu_MPD_Control\certificados"
$certPath = "$certFolder\mi_certificado.pfx"
$password = ConvertTo-SecureString -String "<PASSWORD>" -Force -AsPlainText

# Crear carpeta si no existe
if (-not (Test-Path $certFolder)) { New-Item -ItemType Directory -Path $certFolder }

# Crear certificado auto-firmado **para firma de código**
$cert = New-SelfSignedCertificate `
    -DnsName "LuMPDControllerTest" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -FriendlyName $certName `
    -Type CodeSigningCert `
    -KeyExportPolicy Exportable `
    -KeySpec Signature `
    -NotAfter (Get-Date).AddYears(5)

# Exportarlo a PFX
Export-PfxCertificate `
    -Cert "Cert:\CurrentUser\My\$($cert.Thumbprint)" `
    -FilePath $certPath `
    -Password $password

Write-Host "Certificado de firma generado en $certPath"

# Importarlo a TrustedPublisher (opcional)
Import-PfxCertificate `
    -FilePath $certPath `
    -CertStoreLocation Cert:\CurrentUser\TrustedPublisher `
    -Password $password `
    -Exportable

Write-Host "Certificado importado en TrustedPublisher"
