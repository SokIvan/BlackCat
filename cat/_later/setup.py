from cx_Freeze import setup, Executable
import sys
import os

# Включаем необходимые файлы
include_files = [
    "config.txt",
    "face_dataset/",
    "scripts/",
    "client/",
    "models/",
    "known_faces_db/"
]

# Исключаем ненужные модули
excludes = [
    "tkinter.test", 
    "pydoc_data", 
    "distutils",
    "setuptools",
    "email"
]

build_options = {
    "includes": [
        "tkinter", 
        "PIL",
        "cv2",
        "numpy",
        "mediapipe"
    ],
    "excludes": excludes,
    "include_files": include_files,
    "optimize": 2
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Для GUI приложения без консоли

executables = [
    Executable(
        "BlackCat.py",
        base=base,
        target_name="BlackCat.exe",
        icon="blackcat.ico"  # Можно добавить иконку
    )
]

setup(
    name="BlackCat",
    version="1.0.0",
    description="Система охраны компьютера с распознаванием лиц",
    options={"build_exe": build_options},
    executables=executables
)