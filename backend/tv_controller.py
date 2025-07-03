# TV Controller

import logging
import os
import traceback
from typing import Optional, Dict, Any
from samsungtvws.async_art import SamsungTVAsyncArt
import requests
import json
import asyncio

logger = logging.getLogger(__name__)

class TvController:
    """
    Contrôleur hybride pour TV Samsung Frame qui utilise l'API directe en premier,
    puis SmartThings API comme fallback.
    """
    
    def __init__(self, tv_ip: str, smartthings_token: Optional[str] = None, device_id: Optional[str] = None):
        self.tv_ip = tv_ip
        self.smartthings_token = smartthings_token
        self.device_id = device_id
        self.direct_client: Optional[SamsungTVAsyncArt] = None
        self.smartthings_base_url = "https://api.smartthings.com/v1"
        
    async def get_direct_client(self) -> Optional[SamsungTVAsyncArt]:
        """Obtient le client direct, le crée si nécessaire"""
        if self.direct_client is None:
            try:
                logger.info(f"Création du client direct vers {self.tv_ip}")
                self.direct_client = SamsungTVAsyncArt(host=self.tv_ip, port=8002)
                await self.direct_client.start_listening()
                logger.info("Client direct créé avec succès")
            except Exception as e:
                logger.error(f"Erreur création client direct: {e}")
                return None
        return self.direct_client
    
    async def _smartthings_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Effectue une requête vers l'API SmartThings"""
        if not self.smartthings_token:
            logger.error("Token SmartThings manquant")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.smartthings_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.smartthings_base_url}/{endpoint}"
        
        try:
            # Utiliser asyncio.create_task pour exécuter la requête HTTP synchrone
            loop = asyncio.get_event_loop()
            
            def make_request():
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, timeout=10)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                elif method.upper() == "PUT":
                    response = requests.put(url, headers=headers, json=data, timeout=10)
                else:
                    logger.error(f"Méthode HTTP non supportée: {method}")
                    return None
                    
                response.raise_for_status()
                return response.json()
            
            # Exécuter dans un thread séparé pour ne pas bloquer l'event loop
            result = await loop.run_in_executor(None, make_request)
            return result
            
        except Exception as e:
            logger.error(f"Erreur SmartThings API {method} {endpoint}: {e}")
            return None
    
    async def find_device_id(self) -> Optional[str]:
        """Trouve automatiquement l'ID du device TV Samsung Frame"""
        if self.device_id:
            return self.device_id
            
        try:
            devices = await self._smartthings_request("GET", "devices")
            if not devices or "items" not in devices:
                logger.error("Impossible de récupérer la liste des appareils")
                return None
                
            for device in devices["items"]:
                # Recherche d'une TV Samsung Frame
                if (device.get("name", "").lower().find("frame") != -1 or 
                    device.get("label", "").lower().find("frame") != -1 or
                    device.get("deviceTypeName", "").lower().find("tv") != -1):
                    
                    logger.info(f"Device trouvé: {device.get('name', device.get('label', 'Unknown'))}")
                    self.device_id = device["deviceId"]
                    return self.device_id
                    
            logger.warning("Aucun device Frame trouvé automatiquement")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche du device: {e}")
            return None
    
    async def supported(self) -> bool:
        """Vérifie si la TV supporte l'Art Mode"""
        # Essai méthode directe
        try:
            client = await self.get_direct_client()
            if client:
                result = await client.supported()
                logger.info(f"Art Mode supporté (méthode directe): {result}")
                return result
        except Exception as e:
            logger.warning(f"Erreur méthode directe pour supported(): {e}")
        
        # Fallback SmartThings
        try:
            device_id = await self.find_device_id()
            if not device_id:
                return False
                
            # Vérifier les capabilities du device
            capabilities = await self._smartthings_request("GET", f"devices/{device_id}")
            if capabilities and "components" in capabilities:
                # Recherche de capabilities liées à l'art mode
                for component in capabilities["components"]:
                    if "capabilities" in component:
                        for cap in component["capabilities"]:
                            if "art" in cap.get("id", "").lower():
                                logger.info("Art Mode supporté (SmartThings)")
                                return True
                                
            logger.info("Art Mode non détecté via SmartThings")
            return False
            
        except Exception as e:
            logger.error(f"Erreur SmartThings pour supported(): {e}")
            return False
    
    async def upload_image(self, image_data: bytes, file_type: str = "JPEG", matte: str = "none") -> Optional[str]:
        """Upload une image vers la TV"""
        # Essai méthode directe
        try:
            client = await self.get_direct_client()
            if client:
                logger.info("Tentative upload image (méthode directe)")
                remote_filename = await client.upload(image_data, file_type=file_type, matte=matte)
                logger.info(f"Upload réussi (méthode directe): {remote_filename}")
                return remote_filename
        except Exception as e:
            logger.warning(f"Erreur méthode directe pour upload(): {e}")
        
        # Fallback SmartThings
        # Note: SmartThings ne supporte pas l'upload direct d'images personnalisées
        # pour l'Art Mode. Cette fonctionnalité nécessite l'API directe.
        logger.error("Upload d'image non supporté via SmartThings API")
        return None
    
    async def select_image(self, remote_filename: str, show: bool = True) -> bool:
        """Sélectionne une image sur la TV"""
        # Essai méthode directe
        try:
            client = await self.get_direct_client()
            if client:
                logger.info(f"Tentative sélection image (méthode directe): {remote_filename}")
                await client.select_image(remote_filename, show=show)
                logger.info("Sélection image réussie (méthode directe)")
                return True
        except Exception as e:
            logger.warning(f"Erreur méthode directe pour select_image(): {e}")
        
        # Fallback SmartThings
        try:
            device_id = await self.find_device_id()
            if not device_id:
                return False
                
            # Utiliser la commande SmartThings pour changer l'art
            command_data = {
                "commands": [
                    {
                        "component": "main",
                        "capability": "custom.picturemode",
                        "command": "setPictureMode",
                        "arguments": ["Art"]
                    }
                ]
            }
            
            result = await self._smartthings_request("POST", f"devices/{device_id}/commands", command_data)
            if result:
                logger.info("Mode Art activé via SmartThings")
                return True
                
        except Exception as e:
            logger.error(f"Erreur SmartThings pour select_image(): {e}")
        
        return False
    
    async def get_current_art(self) -> Optional[Dict]:
        """Récupère l'art actuellement affiché"""
        # Essai méthode directe
        try:
            client = await self.get_direct_client()
            if client:
                logger.info("Tentative récupération art actuel (méthode directe)")
                current = await client.get_current()
                logger.info(f"Art actuel récupéré (méthode directe): {current}")
                return current
        except Exception as e:
            logger.warning(f"Erreur méthode directe pour get_current(): {e}")
        
        # Fallback SmartThings
        try:
            device_id = await self.find_device_id()
            if not device_id:
                return None
                
            # Récupérer le statut du device
            status = await self._smartthings_request("GET", f"devices/{device_id}/status")
            if status and "components" in status:
                # Recherche d'informations sur le mode actuel
                for component in status["components"]:
                    if "pictureMode" in component:
                        return {"mode": component["pictureMode"]["value"]}
                        
        except Exception as e:
            logger.error(f"Erreur SmartThings pour get_current(): {e}")
        
        return None
    
    async def get_device_info(self) -> Optional[Dict]:
        """Récupère les informations du device"""
        # Essai méthode directe
        try:
            client = await self.get_direct_client()
            if client:
                logger.info("Tentative récupération info device (méthode directe)")
                info = await client.get_device_info()
                if info:
                    logger.info("Info device récupérée (méthode directe)")
                    return info
        except Exception as e:
            logger.warning(f"Erreur méthode directe pour get_device_info(): {e}")
        
        # Fallback SmartThings
        try:
            device_id = await self.find_device_id()
            if not device_id:
                return None
                
            device_info = await self._smartthings_request("GET", f"devices/{device_id}")
            if device_info:
                logger.info("Info device récupérée (SmartThings)")
                return device_info
                
        except Exception as e:
            logger.error(f"Erreur SmartThings pour get_device_info(): {e}")
        
        return None
    
    async def send_key(self, key: str) -> bool:
        """Envoie une touche à la TV"""
        # Essai méthode directe
        try:
            client = await self.get_direct_client()
            if client and hasattr(client, 'send_key'):
                logger.info(f"Tentative envoi touche (méthode directe): {key}")
                await client.send_key(key)
                logger.info("Touche envoyée (méthode directe)")
                return True
        except Exception as e:
            logger.warning(f"Erreur méthode directe pour send_key(): {e}")
        
        # Fallback SmartThings
        try:
            device_id = await self.find_device_id()
            if not device_id:
                return False
                
            # Mapper les touches vers les commandes SmartThings
            key_mapping = {
                "KEY_POWER": "power",
                "KEY_POWEROFF": "off",
                "KEY_POWERON": "on",
                "KEY_NETFLIX": "Netflix",
                "KEY_HOME": "home",
                "KEY_MENU": "menu",
                "KEY_UP": "up",
                "KEY_DOWN": "down",
                "KEY_LEFT": "left",
                "KEY_RIGHT": "right",
                "KEY_ENTER": "enter",
                "KEY_RETURN": "back"
            }
            
            smartthings_key = key_mapping.get(key, key.replace("KEY_", "").lower())
            
            command_data = {
                "commands": [
                    {
                        "component": "main",
                        "capability": "mediaInputSource",
                        "command": "setInputSource",
                        "arguments": [smartthings_key]
                    }
                ]
            }
            
            result = await self._smartthings_request("POST", f"devices/{device_id}/commands", command_data)
            if result:
                logger.info(f"Touche envoyée via SmartThings: {key}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur SmartThings pour send_key(): {e}")
        
        return False
    
    async def close(self):
        """Ferme les connexions"""
        if self.direct_client:
            try:
                await self.direct_client.close()
                logger.info("Client direct fermé")
            except Exception as e:
                logger.error(f"Erreur fermeture client direct: {e}")
