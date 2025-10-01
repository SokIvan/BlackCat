@echo off
chcp 65001 >nul
echo 🐱 Сборка BlackCat.exe...
echo.

:: Проверяем наличие cx_Freeze
python -c "import cx_Freeze" 2>nul
if errorlevel 1 (
    echo ❌ cx_Freeze не установлен!
    echo Установка cx_Freeze...
    pip install cx_Freeze
)

:: Собираем exe файл
echo 📦 Сборка исполняемого файла...
python setup.py build

if errorlevel 1 (
    echo ❌ Ошибка сборки!
    pause
    exit /b 1
)

echo.
echo ✅ Сборка завершена успешно!
echo 📁 Исполняемый файл находится в папке: build\
echo.
echo 🚀 Для запуска: BlackCat.exe
echo.
pause