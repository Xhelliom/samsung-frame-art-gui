#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration SmartThings
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from tv_controller import TvController

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_smartthings_config():
    """Teste la configuration SmartThings"""
    
    # Charger les variables d'environnement
    load_dotenv()
    
    tv_ip = os.getenv("TV_IP")
    smartthings_token = os.getenv("SMARTTHINGS_TOKEN")
    device_id = os.getenv("SMARTTHINGS_DEVICE_ID")
    
    print("=== Test de configuration SmartThings ===")
    print(f"TV_IP: {tv_ip}")
    print(f"SMARTTHINGS_TOKEN: {'✓ Configuré' if smartthings_token else '✗ Manquant'}")
    print(f"SMARTTHINGS_DEVICE_ID: {'✓ Configuré' if device_id else '✗ Sera détecté automatiquement'}")
    print()
    
    if not tv_ip:
        print("❌ TV_IP manquant dans le fichier .env")
        return
    
    if not smartthings_token:
        print("❌ SMARTTHINGS_TOKEN manquant dans le fichier .env")
        print("Voir SMARTTHINGS_CONFIG.md pour la configuration")
        return
    
    # Créer le contrôleur TV
    tv_controller = TvController(
        tv_ip=tv_ip,
        smartthings_token=smartthings_token,
        device_id=device_id
    )
    
    try:
        print("🔍 Test de détection automatique du device...")
        detected_device_id = await tv_controller.find_device_id()
        if detected_device_id:
            print(f"✅ Device détecté: {detected_device_id}")
        else:
            print("⚠️ Aucun device Frame détecté automatiquement")
            print("   Vérifiez que votre TV est connectée à SmartThings")
        
        print("\n🔍 Test de support Art Mode...")
        art_supported = await tv_controller.supported()
        if art_supported:
            print("✅ Art Mode supporté")
        else:
            print("⚠️ Art Mode non détecté")
        
        print("\n🔍 Test de récupération d'informations device...")
        device_info = await tv_controller.get_device_info()
        if device_info:
            print("✅ Informations device récupérées")
            if isinstance(device_info, dict):
                print(f"   Nom: {device_info.get('name', 'N/A')}")
                print(f"   Label: {device_info.get('label', 'N/A')}")
                print(f"   Type: {device_info.get('deviceTypeName', 'N/A')}")
        else:
            print("⚠️ Impossible de récupérer les informations device")
        
        print("\n🔍 Test de récupération de l'état actuel...")
        current_art = await tv_controller.get_current_art()
        if current_art:
            print("✅ État actuel récupéré")
            print(f"   Détails: {current_art}")
        else:
            print("⚠️ Impossible de récupérer l'état actuel")
        
        print("\n✅ Tests terminés avec succès!")
        print("Le système SmartThings est configuré et fonctionne en tant que fallback.")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        logger.error(f"Erreur détaillée: {e}", exc_info=True)
    
    finally:
        await tv_controller.close()

def main():
    """Fonction principale"""
    try:
        asyncio.run(test_smartthings_config())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main() 