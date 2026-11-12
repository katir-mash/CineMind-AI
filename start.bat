@echo off
cd /d "%~dp0"
py -3 app.py
if errorlevel 1 (
  echo Ошибка запуска. Проверьте установку Python 3.10+ и tkinter.
  pause
)
