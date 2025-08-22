
@echo off
echo Aguardando o aplicativo fechar...
taskkill /F /PID 19528 > nul 2>&1
timeout /t 2 /nobreak > nul

echo Substituindo arquivos...
move /Y "D:\Importantes\MonitorCriptomoedas3.2.1\venv\Scripts\python.exe" "D:\Importantes\MonitorCriptomoedas3.2.1\python.old"
move /Y "D:\Importantes\MonitorCriptomoedas3.2.1\update.exe" "D:\Importantes\MonitorCriptomoedas3.2.1\venv\Scripts\python.exe"

echo Limpando...
del "D:\Importantes\MonitorCriptomoedas3.2.1\python.old" > nul 2>&1

echo Reiniciando o aplicativo...
start "" "D:\Importantes\MonitorCriptomoedas3.2.1\venv\Scripts\python.exe"

(goto) 2>nul & del "%~f0"
