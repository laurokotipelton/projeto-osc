#!/bin/bash

echo "✅ Iniciando build com PyInstaller..."

# Remove pastas antigas do PyInstaller se existirem
rm -rf build dist __pycache__ *.spec

# Gera o executável
pyinstaller --noconfirm --onefile --add-data "app/templates:app/templates" --add-data "app/static:app/static" start.py

echo "✅ Build finalizado! O executável está em: dist/start"
