@echo off
pyinstaller --onefile --windowed --icon=mypad.ico --add-data "mypad.ico;." sticky_note.py
pause
