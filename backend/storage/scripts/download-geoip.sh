#!/bin/bash
# Script para descargar GeoLite2-Country database

set -e

echo "📥 Descargando GeoLite2-Country database..."

# Crear directorio data si no existe
mkdir -p data

# Descargar base de datos
cd data

if [ -f "GeoLite2-Country.mmdb" ]; then
    echo "⚠️  GeoLite2-Country.mmdb ya existe"
    read -p "¿Descargar nueva versión? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "✅ Usando versión existente"
        exit 0
    fi
    rm GeoLite2-Country.mmdb
fi

echo "⬇️  Descargando desde GitHub..."
wget -q --show-progress https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb

if [ -f "GeoLite2-Country.mmdb" ]; then
    SIZE=$(du -h GeoLite2-Country.mmdb | cut -f1)
    echo "✅ Descarga completa: GeoLite2-Country.mmdb ($SIZE)"
else
    echo "❌ Error en la descarga"
    exit 1
fi

echo ""
echo "🎉 GeoIP database lista para usar"
echo "📍 Ubicación: $(pwd)/GeoLite2-Country.mmdb"
