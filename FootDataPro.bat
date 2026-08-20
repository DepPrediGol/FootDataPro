@echo off
title Actualizar FootDataPro
echo ====================================================
echo    SUBIENDO CAMBIOS DE FOOTDATAPRO A GITHUB
echo ====================================================
echo.

:: 1. Descarga cambios previos de GitHub si existen
git pull origin main --rebase

:: 2. Prepara todos los archivos locales
git add .

:: 3. Pide descripción del cambio
set /p mensaje="Descripcion del cambio (o presiona ENTER): "
if "%mensaje%"=="" set mensaje=Actualizacion FootDataPro %date% %time%

:: 4. Guarda y sube a GitHub
git commit -m "%mensaje%"
git push origin main

echo.
echo ====================================================
echo  ¡Listo! Cambios subidos a GitHub.
echo  FootDataPro se actualizara en linea en segundos.
echo ====================================================
echo.
pause