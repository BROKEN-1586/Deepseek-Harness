@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
"C:\Users\36578\AppData\Local\Programs\Python\Python314\python.exe" "D:\Clearn\tools\followup.py" %*
if "%~1"=="" pause
