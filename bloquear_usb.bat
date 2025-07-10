@echo off
:: Executa como administrador
REG ADD "HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR" /v Start /t REG_DWORD /d 4 /f
echo Dispositivos de armazenamento USB foram bloqueados.
pause