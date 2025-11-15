#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_qr.py - Génère un QR code pour accéder au serveur depuis mobile
"""

import qrcode
import socket

# Obtenir l'IP locale
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# Configuration
local_ip = get_local_ip()
web_port = 3000
api_port = 8000

# URLs
web_url = f"http://{local_ip}:{web_port}"
api_url = f"http://{local_ip}:{api_port}"

print("=" * 60)
print("🔗 GÉNÉRATION DES QR CODES POUR CONNEXION MOBILE")
print("=" * 60)
print(f"\n📍 IP locale détectée: {local_ip}")
print(f"\n🌐 Interface Web: {web_url}")
print(f"🔌 API Backend: {api_url}")

# Générer QR code pour interface web
print("\n📱 Génération du QR code pour l'interface web...")
qr_web = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr_web.add_data(web_url)
qr_web.make(fit=True)

img_web = qr_web.make_image(fill_color="black", back_color="white")
img_web.save("qr_code_web.png")
print(f"✅ QR code sauvegardé: qr_code_web.png")

# Générer QR code pour API
print("\n📱 Génération du QR code pour l'API...")
qr_api = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr_api.add_data(api_url)
qr_api.make(fit=True)

img_api = qr_api.make_image(fill_color="black", back_color="white")
img_api.save("qr_code_api.png")
print(f"✅ QR code sauvegardé: qr_code_api.png")

# Afficher QR code dans le terminal
print("\n" + "=" * 60)
print("📱 QR CODE POUR INTERFACE WEB (Scanner avec votre téléphone)")
print("=" * 60)
qr_web.print_ascii(invert=True)

print("\n" + "=" * 60)
print("📱 QR CODE POUR API BACKEND")
print("=" * 60)
qr_api.print_ascii(invert=True)

print("\n" + "=" * 60)
print("📋 INSTRUCTIONS")
print("=" * 60)
print("1. Assurez-vous que votre téléphone est sur le même réseau Wi-Fi")
print("2. Scannez le QR code ci-dessus avec votre téléphone")
print("3. Vous serez redirigé vers l'interface web")
print(f"\n   OU visitez directement: {web_url}")
print("\n💡 Si vous ne voyez pas les QR codes dans le terminal:")
print("   - Ouvrez les images: qr_code_web.png et qr_code_api.png")
print("=" * 60)
