@echo off
cd /d "%~dp0"
python rowwidthbeacon.py --gui
if errorlevel 1 pause
