@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ====================================
echo Запуск программы уведомлений календаря
echo ====================================

:: Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не установлен!
    echo Пожалуйста, установите Python с сайта https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Проверяем наличие файла .env
if not exist .env (
    echo Ошибка: Файл .env не найден!
    echo Пожалуйста, создайте файл .env с необходимыми настройками
    pause
    exit /b 1
)

:: Проверяем наличие виртуального окружения
if not exist venv (
    echo Создание виртуального окружения...
    python -m venv venv
    if errorlevel 1 (
        echo Ошибка при создании виртуального окружения!
        pause
        exit /b 1
    )
)

:: Активируем виртуальное окружение
call venv\Scripts\activate.bat

:: Устанавливаем зависимости
echo Установка зависимостей...
pip install -r requirements.txt
if errorlevel 1 (
    echo Ошибка при установке зависимостей!
    pause
    exit /b 1
)

:: Очищаем консоль
cls

:: Запускаем программу
echo ====================================
echo Программа запущена. Для остановки нажмите Ctrl+C
echo ====================================
echo.

:: Запускаем Python скрипт с выводом логов в консоль
python main.py

:: Деактивируем виртуальное окружение при выходе
deactivate

pause 