@echo off
:: Script para forçar instalação de extensão no Chrome e Edge

:: Defina o ID da extensão
set EXT_ID1=blaaajhemilngeeffpbfkdjjoefldkok
set EXT_ID2=hnncfhodpmpjchmmcnimoimkcojdmfhl
set UPDATE_URL1=https://clients2.google.com/service/update2/crx
set UPDATE_URL2=https://edge.microsoft.com/extensionwebstorebase/v1/crx

:: Chrome (HKLM)
REG ADD "HKLM\Software\Policies\Google\Chrome\ExtensionInstallForcelist" /v 1 /t REG_SZ /d "%EXT_ID1%;%UPDATE_URL1%" /f

:: Edge (HKLM)
REG ADD "HKLM\Software\Policies\Microsoft\Edge\ExtensionInstallForcelist" /v 1 /t REG_SZ /d "%EXT_ID2%;%UPDATE_URL2%" /f

echo Extensões forçadas no Chrome e Edge com sucesso.

SETLOCAL

:: Caminho padrão da instalação do Firefox
SET FF_PATH="C:\Program Files\Mozilla Firefox\distribution"

:: Cria a pasta "distribution" se não existir
IF NOT EXIST %FF_PATH% (
    mkdir %FF_PATH%
)

:: Cria o arquivo policies.json
(
echo {
echo   "policies": {
echo     "Extensions": {
echo       "Install": [
echo         "https://addons.mozilla.org/firefox/downloads/file/4507296/leechblock_ng-1.7.xpi"
echo       ],
echo       "Locked": [
echo         "leechblockng@proginosko.com"
echo       ]
echo     }
echo   }
echo }
) > %FF_PATH%\policies.json

echo policies.json criado com sucesso em %FF_PATH%
pause