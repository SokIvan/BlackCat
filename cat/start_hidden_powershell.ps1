# Запуск от Администратора: PowerShell -> "Set-ExecutionPolicy RemoteSigned"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptPath
Start-Process -FilePath "python" -ArgumentList "main.py" -WindowStyle Hidden