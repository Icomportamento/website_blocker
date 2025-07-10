@echo off
SETLOCAL

echo Revertendo pol�ticas de extens�es for�adas...

:: =============================
:: Chrome - Remover extens�o for�ada
:: =============================
REG DELETE "HKLM\Software\Policies\Google\Chrome\ExtensionInstallForcelist" /f

:: =============================
:: Edge - Remover extens�o for�ada
:: =============================
REG DELETE "HKLM\Software\Policies\Microsoft\Edge\ExtensionInstallForcelist" /f

:: =============================
:: Firefox - Remover policies.json
:: =============================

:: Caminhos comuns do Firefox (64 bits e 32 bits)
SET FF_PATH1="C:\Program Files\Mozilla Firefox\distribution\policies.json"
SET FF_PATH2="C:\Program Files (x86)\Mozilla Firefox\distribution\policies.json"

IF EXIST %FF_PATH1% (
    DEL /F /Q %FF_PATH1%
    echo policies.json removido de Program Files.
)

IF EXIST %FF_PATH2% (
    DEL /F /Q %FF_PATH2%
    echo policies.json removido de Program Files (x86).
)

echo Todas as altera��es foram revertidas.
pause