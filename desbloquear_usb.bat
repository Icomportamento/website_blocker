@echo off
:: Executa como administrador
REG ADD "HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR" /v Start /t REG_DWORD /d 3 /f
echo Dispositivos de armazenamento USB foram desbloqueados.
pause