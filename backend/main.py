from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from typing import List
from dotenv import load_dotenv
import requests
from samsungtvws.async_art import SamsungTVAsyncArt
from fastapi.staticfiles import StaticFiles
import logging
import asyncio
import base64
import traceback
from .tv_controller import TvController

# Load environment variables (.env at project root)
load_dotenv()

TV_IP = os.getenv("TV_IP")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
SMARTTHINGS_TOKEN = os.getenv("SMARTTHINGS_TOKEN")
SMARTTHINGS_DEVICE_ID = os.getenv("SMARTTHINGS_DEVICE_ID")

if not TV_IP:
    raise RuntimeError("L'adresse IP de la TV doit être définie dans la variable d'environnement TV_IP")

app = FastAPI(title="Samsung Frame Art API")

# Enable CORS for the frontend (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware pour capturer les erreurs non gérées
@app.middleware("http")
async def catch_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(f"Erreur non gérée dans {request.method} {request.url}: {exc}")
        logger.error(f"Type d'erreur: {type(exc).__name__}")
        logger.error(f"Traceback complet:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {exc}")

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter des logs plus détaillés pour les erreurs
import traceback

# Instantiate the TV controller once
_tv_controller: TvController | None = None


async def get_tv_controller() -> TvController:
    global _tv_controller
    if _tv_controller is None:
        logger.info(f"Création du contrôleur TV vers {TV_IP}")
        try:
            _tv_controller = TvController(
                tv_ip=TV_IP,
                smartthings_token=SMARTTHINGS_TOKEN,
                device_id=SMARTTHINGS_DEVICE_ID
            )
            logger.info("Contrôleur TV créé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création du contrôleur TV: {e}")
            logger.error(f"Type d'erreur: {type(e).__name__}")
            logger.error(f"Traceback complet:\n{traceback.format_exc()}")
            raise
        logger.info("Contrôleur TV créé avec succès")
    return _tv_controller

# Base directory where images are stored
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# File that persists the mapping between local file and remote filename
UPLOAD_MAP_PATH = os.path.join(os.path.dirname(__file__), "uploaded_files.json")

# Load persisted mapping
if os.path.isfile(UPLOAD_MAP_PATH):
    with open(UPLOAD_MAP_PATH, "r", encoding="utf-8") as fp:
        uploaded_files: List[dict] = json.load(fp)
else:
    uploaded_files = []


def save_uploaded_map():
    with open(UPLOAD_MAP_PATH, "w", encoding="utf-8") as fp:
        json.dump(uploaded_files, fp, ensure_ascii=False, indent=2)


class ImageItem(BaseModel):
    file: str  # local filepath
    remote_filename: str | None = None  # identifier on the TV


@app.get("/api/images", response_model=List[ImageItem])
async def list_images():
    """Liste toutes les images locales, ainsi que leur remote_filename si déjà téléversées."""
    logger.info("Récupération de la liste des images locales")
    # Scan local files (jpg/png)
    local_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    logger.info(f"Trouvé {len(local_files)} fichiers locaux")
    
    items: List[ImageItem] = []
    for fname in local_files:
        full_path = os.path.join(IMAGE_DIR, fname)
        mapping = next((m for m in uploaded_files if os.path.abspath(m["file"]) == os.path.abspath(full_path)), None)
        items.append(
            ImageItem(
                file=fname,
                remote_filename=mapping["remote_filename"] if mapping else None,
            )
        )
    logger.info(f"Retour de {len(items)} éléments")
    return items


@app.post("/api/upload", response_model=ImageItem)
async def upload_image(file: UploadFile = File(...)):
    """Téléverse une nouvelle image localement seulement."""
    logger.info(f"Début upload: {file.filename}, type: {file.content_type}")
    
    if file.content_type not in ["image/jpeg", "image/png"]:
        logger.error(f"Type de fichier non supporté: {file.content_type}")
        raise HTTPException(status_code=400, detail="Seuls les fichiers JPEG ou PNG sont autorisés")

    # Save file locally
    ext = ".jpg" if file.content_type == "image/jpeg" else ".png"
    filename = file.filename or f"image{ext}"
    local_path = os.path.join(IMAGE_DIR, filename)
    i = 1
    while os.path.exists(local_path):
        filename = f"{os.path.splitext(file.filename)[0]}_{i}{ext}"
        local_path = os.path.join(IMAGE_DIR, filename)
        i += 1

    logger.info(f"Sauvegarde locale: {local_path}")
    contents = await file.read()
    logger.info(f"Taille du fichier: {len(contents)} bytes")
    
    with open(local_path, "wb") as fp:
        fp.write(contents)

    logger.info(f"Upload local terminé avec succès: {filename}")
    return ImageItem(file=filename, remote_filename=None)


class SendToTVRequest(BaseModel):
    filename: str


@app.post("/api/send-to-tv", response_model=ImageItem)
async def send_to_tv(req: SendToTVRequest):
    """Envoie une image locale vers la TV et la marque comme remote."""
    logger.info(f"Envoi vers TV demandé: {req.filename}")
    
    local_path = os.path.join(IMAGE_DIR, req.filename)
    if not os.path.exists(local_path):
        logger.error(f"Fichier local non trouvé: {local_path}")
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    # Vérifier si déjà envoyé
    existing_mapping = next((m for m in uploaded_files if os.path.abspath(m["file"]) == os.path.abspath(local_path)), None)
    if existing_mapping:
        logger.info(f"Image déjà envoyée, remote_filename: {existing_mapping['remote_filename']}")
        return ImageItem(file=req.filename, remote_filename=existing_mapping["remote_filename"])
    
    # Lire le fichier
    logger.info(f"Lecture du fichier: {local_path}")
    with open(local_path, "rb") as fp:
        contents = fp.read()
    
    logger.info(f"Taille du fichier: {len(contents)} bytes")
    
    # Upload to TV
    logger.info("Début envoi vers la TV")
    tv_controller = await get_tv_controller()
    try:
        # Vérifier si la TV supporte l'art mode
        logger.info("Vérification du support Art Mode")
        if not await tv_controller.supported():
            logger.error("TV ne supporte pas l'Art Mode")
            raise HTTPException(status_code=400, detail="Cette TV ne supporte pas l'Art Mode")
        
        # Vérifier la taille du fichier (limite Samsung ~10MB)
        if len(contents) > 10 * 1024 * 1024:
            logger.error(f"Fichier trop volumineux: {len(contents)} bytes")
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10MB)")

        # Déterminer le type de fichier
        ext = os.path.splitext(req.filename)[1].lower()
        logger.info(f"Envoi {ext} vers la TV...")
        
        if ext in [".jpg", ".jpeg"]:
            remote_filename = await tv_controller.upload_image(contents, file_type="JPEG", matte="none")
        elif ext == ".png":
            remote_filename = await tv_controller.upload_image(contents, file_type="PNG", matte="none")
        else:
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")
        
        if remote_filename:
            logger.info(f"Envoi réussi, remote_filename: {remote_filename}")
        else:
            raise HTTPException(status_code=500, detail="Échec de l'upload via les deux méthodes (directe et SmartThings)")
    except Exception as exc:
        logger.error(f"Erreur envoi TV: {exc}")
        logger.error(f"Type d'erreur: {type(exc).__name__}")
        logger.error(f"Traceback complet:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi vers la TV: {exc}")

    # Persist mapping
    logger.info("Sauvegarde du mapping local/remote")
    uploaded_files.append({"file": local_path, "remote_filename": remote_filename})
    save_uploaded_map()

    logger.info(f"Envoi vers TV terminé avec succès: {req.filename}")
    return ImageItem(file=req.filename, remote_filename=remote_filename)


class SelectImageRequest(BaseModel):
    remote_filename: str


@app.post("/api/set-image")
async def set_image(req: SelectImageRequest):
    logger.info(f"Sélection d'image: {req.remote_filename}")
    tv_controller = await get_tv_controller()
    try:
        logger.info("Envoi de la commande select_image à la TV")
        success = await tv_controller.select_image(req.remote_filename)
        if success:
            logger.info("Image sélectionnée avec succès")
            return {"status": "success", "message": "Image sélectionnée sur la TV"}
        else:
            raise HTTPException(status_code=500, detail="Échec de la sélection via les deux méthodes (directe et SmartThings)")
    except Exception as exc:
        logger.error(f"Erreur lors de la sélection: {exc}")
        logger.error(f"Type d'erreur: {type(exc).__name__}")
        logger.error(f"Traceback complet:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sélection de l'image: {exc}")


@app.get("/api/current-image")
async def get_current_image():
    """Récupère l'image actuellement affichée sur la TV."""
    logger.info("Récupération de l'image actuelle")
    tv_controller = await get_tv_controller()
    try:
        # Essayer de récupérer l'image actuelle
        current = await tv_controller.get_current_art()
        logger.info(f"Image actuelle récupérée: {current}")
        
        if current:
            # Pour SmartThings, on a juste le mode
            if "mode" in current:
                return {
                    "status": "smartthings_mode",
                    "mode": current["mode"],
                    "message": "Mode actuel récupéré via SmartThings"
                }
            else:
                # Pour l'API directe, on a plus d'informations
                return current
        else:
            logger.info("Aucune information d'art actuel récupérée")
            return {
                "status": "no_current_image",
                "message": "Aucune image actuellement affichée sur la TV",
                "content_id": None
            }
    except AssertionError:
        # La TV n'a pas d'image actuellement affichée ou n'est pas en Art Mode
        logger.info("Aucune image actuellement affichée (AssertionError)")
        return {
            "status": "no_current_image",
            "message": "Aucune image actuellement affichée sur la TV",
            "content_id": None
        }
    except Exception as exc:
        logger.error(f"Erreur récupération image actuelle: {exc}")
        logger.error(f"Type d'erreur: {type(exc).__name__}")
        logger.error(f"Traceback complet:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'image actuelle: {exc}")


@app.get("/api/search-unsplash")
async def search_unsplash(query: str):
    logger.info(f"Recherche Unsplash: '{query}'")
    if not UNSPLASH_ACCESS_KEY:
        logger.error("Clé API Unsplash manquante")
        raise HTTPException(status_code=500, detail="Clé API Unsplash manquante")

    url = "https://api.unsplash.com/search/photos"
    params = {"query": query, "client_id": UNSPLASH_ACCESS_KEY, "per_page": 30}
    logger.info(f"Appel API Unsplash: {url}")
    r = requests.get(url, params=params, timeout=10)
    logger.info(f"Réponse Unsplash: status={r.status_code}")
    if r.status_code != 200:
        logger.error(f"Erreur API Unsplash: {r.status_code} - {r.text}")
        raise HTTPException(status_code=r.status_code, detail="Erreur lors de la recherche Unsplash")

    data = r.json()
    logger.info(f"Résultats Unsplash: {len(data.get('results', []))} photos")
    # Return subset of data to limit payload size
    results = [
        {
            "id": p["id"],
            "description": p.get("description") or p.get("alt_description"),
            "urls": p["urls"],
            "user": {
                "name": p["user"]["name"],
                "profile": p["user"]["links"]["html"],
            },
            "download_location": p["links"].get("download_location"),
        }
        for p in data.get("results", [])
    ]
    return results

# Serve uploaded images statically
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# Endpoint pour récupérer des photos populaires/featured
@app.get("/api/unsplash-featured")
async def unsplash_featured():
    logger.info("Récupération des photos Unsplash populaires")
    if not UNSPLASH_ACCESS_KEY:
        logger.error("Clé API Unsplash manquante")
        raise HTTPException(status_code=500, detail="Clé API Unsplash manquante")

    url = "https://api.unsplash.com/photos"
    params = {"client_id": UNSPLASH_ACCESS_KEY, "per_page": 30, "order_by": "popular"}
    logger.info(f"Appel API Unsplash featured: {url}")
    r = requests.get(url, params=params, timeout=10)
    logger.info(f"Réponse Unsplash featured: status={r.status_code}")
    if r.status_code != 200:
        logger.error(f"Erreur API Unsplash featured: {r.status_code} - {r.text}")
        raise HTTPException(status_code=r.status_code, detail="Erreur Unsplash")

    data = r.json()
    logger.info(f"Photos populaires récupérées: {len(data)} photos")
    results = [
        {
            "id": p["id"],
            "description": p.get("description") or p.get("alt_description"),
            "urls": p["urls"],
            "user": {
                "name": p["user"]["name"],
                "profile": p["user"]["links"]["html"],
            },
            "download_location": p["links"].get("download_location"),
        }
        for p in data
    ]
    return results

@app.get("/api/tv-status")
async def get_tv_status():
    """Diagnostic de l'état de la TV et de ses capacités."""
    logger.info("Diagnostic TV demandé")
    tv_controller = await get_tv_controller()
    try:
        # Test de connexion basique
        logger.info("Test de connexion TV")
        supported = await tv_controller.supported()
        logger.info(f"Art Mode supporté: {supported}")
        
        if not supported:
            return {
                "status": "error",
                "message": "Cette TV ne supporte pas l'Art Mode",
                "art_mode_supported": False
            }
        
        # Récupérer des informations sur l'état actuel
        logger.info("Récupération des informations TV")
        current_art = await tv_controller.get_current_art()
        logger.info(f"Art actuel: {current_art}")
        
        # Récupérer les informations du device
        device_info = await tv_controller.get_device_info()
        logger.info(f"Info device: {device_info}")
        
        return {
            "status": "success",
            "message": "TV connectée et fonctionnelle",
            "tv_ip": TV_IP,
            "art_mode_supported": True,
            "current_art": current_art,
            "device_info": device_info
        }
    except Exception as exc:
        logger.error(f"Erreur diagnostic TV: {exc}")
        return {
            "status": "error",
            "message": f"Erreur de connexion à la TV: {exc}",
            "tv_ip": TV_IP,
            "art_mode_supported": False
        }

# =============================================================================
# ENDPOINTS DE DEBUG
# =============================================================================

@app.get("/api/debug/api-version")
async def debug_api_version():
    """Debug: Récupère les informations du device."""
    logger.info("DEBUG: Récupération info device")
    tv_controller = await get_tv_controller()
    try:
        device_info = await tv_controller.get_device_info()
        logger.info(f"DEBUG: Device info: {device_info}")
        return {"device_info": device_info}
    except Exception as exc:
        logger.error(f"DEBUG: Erreur info device: {exc}")
        return {"error": str(exc)}

@app.get("/api/debug/tv-status")
async def debug_tv_status():
    """Debug: Statut complet de la TV."""
    logger.info("DEBUG: Statut TV complet")
    tv_controller = await get_tv_controller()
    try:
        status = {}
        
        # Support Art Mode
        status["art_supported"] = await tv_controller.supported()
        logger.info(f"DEBUG: Art Mode supporté: {status['art_supported']}")
        
        # Récupérer l'état actuel
        if status["art_supported"]:
            try:
                current_art = await tv_controller.get_current_art()
                status["current_art"] = current_art
                logger.info(f"DEBUG: Art actuel: {current_art}")
            except:
                status["current_art"] = "unknown"
        
        # Informations du device
        try:
            device_info = await tv_controller.get_device_info()
            status["device_info"] = device_info
        except:
            status["device_info"] = "unknown"
        
        return status
    except Exception as exc:
        logger.error(f"DEBUG: Erreur statut TV: {exc}")
        return {"error": str(exc)}

@app.post("/api/debug/set-artmode")
async def debug_set_artmode(request: dict):
    """Debug: Test du système hybride."""
    logger.info("DEBUG: Test du système hybride")
    tv_controller = await get_tv_controller()
    try:
        # Tester les fonctionnalités de base
        supported = await tv_controller.supported()
        device_info = await tv_controller.get_device_info()
        current_art = await tv_controller.get_current_art()
        
        logger.info("DEBUG: Test système hybride réussi")
        return {
            "status": "success", 
            "art_supported": supported,
            "device_info": device_info is not None,
            "current_art": current_art is not None
        }
    except Exception as exc:
        logger.error(f"DEBUG: Erreur test système: {exc}")
        return {"error": str(exc)}

@app.get("/api/debug/available-art")
async def debug_available_art():
    """Debug: Informations sur le système hybride."""
    logger.info("DEBUG: Informations système hybride")
    tv_controller = await get_tv_controller()
    try:
        # Tester toutes les fonctionnalités
        info = {
            "art_supported": await tv_controller.supported(),
            "device_info_available": (await tv_controller.get_device_info()) is not None,
            "current_art_available": (await tv_controller.get_current_art()) is not None,
            "smartthings_token_configured": tv_controller.smartthings_token is not None,
            "device_id_configured": tv_controller.device_id is not None
        }
        
        logger.info(f"DEBUG: Informations système: {info}")
        return info
    except Exception as exc:
        logger.error(f"DEBUG: Erreur informations système: {exc}")
        return {"error": str(exc)}

@app.get("/api/debug/artmode-settings")
async def debug_artmode_settings():
    """Debug: Test détection automatique SmartThings."""
    logger.info("DEBUG: Test détection SmartThings")
    tv_controller = await get_tv_controller()
    try:
        # Tester la détection automatique
        if tv_controller.smartthings_token:
            device_id = await tv_controller.find_device_id()
            return {
                "smartthings_enabled": True,
                "device_auto_detected": device_id is not None,
                "detected_device_id": device_id,
                "configured_device_id": tv_controller.device_id
            }
        else:
            return {
                "smartthings_enabled": False,
                "message": "Token SmartThings non configuré"
            }
    except Exception as exc:
        logger.error(f"DEBUG: Erreur test SmartThings: {exc}")
        return {"error": str(exc)}

@app.post("/api/debug/test-upload")
async def debug_test_upload(request: dict):
    """Debug: Test d'upload avec logs détaillés."""
    filename = request.get("filename")
    if not filename:
        return {"error": "Nom de fichier requis"}
    
    logger.info(f"DEBUG: Test upload pour: {filename}")
    local_path = os.path.join(IMAGE_DIR, filename)
    
    if not os.path.exists(local_path):
        return {"error": "Fichier non trouvé"}
    
    tv_controller = await get_tv_controller()
    try:
        # Lire le fichier
        with open(local_path, "rb") as fp:
            contents = fp.read()
        
        logger.info(f"DEBUG: Fichier lu, taille: {len(contents)} bytes")
        
        # Vérifications préalables
        checks = {}
        checks["file_size"] = len(contents)
        checks["file_size_ok"] = len(contents) <= 10 * 1024 * 1024
        checks["art_supported"] = await tv_controller.supported()
        
        # Obtenir les informations du device
        device_info = await tv_controller.get_device_info()
        checks["device_info"] = device_info is not None
        
        logger.info(f"DEBUG: Vérifications: {checks}")
        
        # Tentative d'upload
        ext = os.path.splitext(filename)[1].lower()
        logger.info(f"DEBUG: Extension détectée: {ext}")
        
        if ext in [".jpg", ".jpeg"]:
            logger.info("DEBUG: Upload JPEG...")
            remote_filename = await tv_controller.upload_image(contents, file_type="JPEG", matte="none")
        elif ext == ".png":
            logger.info("DEBUG: Upload PNG...")
            remote_filename = await tv_controller.upload_image(contents, file_type="PNG", matte="none")
        else:
            return {"error": "Format non supporté"}
        
        if remote_filename:
            logger.info(f"DEBUG: Upload réussi: {remote_filename}")
            
            return {
                "status": "success",
                "remote_filename": remote_filename,
                "checks": checks,
                "file_info": {
                    "filename": filename,
                    "size": len(contents),
                    "extension": ext
                }
            }
        else:
            return {"error": "Échec de l'upload via les deux méthodes"}
        
    except Exception as exc:
        logger.error(f"DEBUG: Erreur test upload: {exc}")
        logger.error(f"DEBUG: Type d'erreur: {type(exc).__name__}")
        logger.error(f"DEBUG: Traceback:\n{traceback.format_exc()}")
        return {"error": str(exc), "error_type": type(exc).__name__}

@app.get("/api/debug/slideshow-status")
async def debug_slideshow_status():
    """Debug: Test complet du système hybride."""
    logger.info("DEBUG: Test complet système hybride")
    tv_controller = await get_tv_controller()
    try:
        # Test complet de toutes les fonctionnalités
        result = {
            "direct_api_test": False,
            "smartthings_test": False,
            "art_supported": False,
            "device_info": False,
            "current_art": False
        }
        
        # Test Art Mode supporté
        try:
            result["art_supported"] = await tv_controller.supported()
        except:
            pass
        
        # Test informations device
        try:
            device_info = await tv_controller.get_device_info()
            result["device_info"] = device_info is not None
        except:
            pass
        
        # Test art actuel
        try:
            current_art = await tv_controller.get_current_art()
            result["current_art"] = current_art is not None
        except:
            pass
        
        # Test détection SmartThings
        if tv_controller.smartthings_token:
            try:
                device_id = await tv_controller.find_device_id()
                result["smartthings_test"] = device_id is not None
            except:
                pass
        
        return result
    except Exception as exc:
        logger.error(f"DEBUG: Erreur test complet: {exc}")
        return {"error": str(exc)}

@app.post("/api/debug/power-on")
async def debug_power_on():
    """Debug: Test envoi de touche Power."""
    logger.info("DEBUG: Test envoi touche Power")
    tv_controller = await get_tv_controller()
    try:
        success = await tv_controller.send_key("KEY_POWER")
        if success:
            logger.info("DEBUG: Touche Power envoyée avec succès")
            return {"status": "success", "message": "Touche Power envoyée"}
        else:
            return {"error": "Échec envoi touche Power via les deux méthodes"}
    except Exception as exc:
        logger.error(f"DEBUG: Erreur envoi touche Power: {exc}")
        return {"error": str(exc)}

@app.post("/api/debug/send-key")
async def debug_send_key(request: dict):
    """Debug: Envoie une touche à la TV."""
    key = request.get("key")
    if not key:
        return {"error": "Clé requise"}
    
    logger.info(f"DEBUG: Envoi touche: {key}")
    tv_controller = await get_tv_controller()
    try:
        success = await tv_controller.send_key(key)
        if success:
            logger.info(f"DEBUG: Touche {key} envoyée")
            return {"status": "success", "key": key}
        else:
            logger.error(f"DEBUG: Échec envoi touche: {key}")
            return {"error": "Échec de l'envoi de la touche via les deux méthodes"}
    except Exception as exc:
        logger.error(f"DEBUG: Erreur envoi touche: {exc}")
        return {"error": str(exc)}

@app.get("/api/debug/device-info")
async def debug_device_info():
    """Debug: Informations sur l'appareil."""
    logger.info("DEBUG: Récupération info device")
    tv_controller = await get_tv_controller()
    try:
        device_info = await tv_controller.get_device_info()
        logger.info(f"DEBUG: Info device récupérées")
        return device_info
    except Exception as exc:
        logger.error(f"DEBUG: Erreur info device: {exc}")
        return {"error": str(exc)}

@app.get("/api/debug/app-list")
async def debug_app_list():
    """Debug: Test connexion SmartThings."""
    logger.info("DEBUG: Test connexion SmartThings")
    tv_controller = await get_tv_controller()
    try:
        if not tv_controller.smartthings_token:
            return {"error": "Token SmartThings non configuré"}
        
        # Test de connexion SmartThings
        device_id = await tv_controller.find_device_id()
        device_info = await tv_controller.get_device_info()
        
        return {
            "smartthings_connection": "OK",
            "device_detected": device_id is not None,
            "device_info_available": device_info is not None,
            "device_id": device_id
        }
    except Exception as exc:
        logger.error(f"DEBUG: Erreur test SmartThings: {exc}")
        return {"error": str(exc)}

@app.post("/api/debug/run-app")
async def debug_run_app(request: dict):
    """Debug: Test envoi de touche personnalisée."""
    key = request.get("key", "KEY_HOME")  # Par défaut KEY_HOME
    
    logger.info(f"DEBUG: Test envoi touche: {key}")
    tv_controller = await get_tv_controller()
    try:
        success = await tv_controller.send_key(key)
        if success:
            logger.info(f"DEBUG: Touche {key} envoyée avec succès")
            return {"status": "success", "key": key}
        else:
            return {"error": f"Échec envoi touche {key} via les deux méthodes"}
    except Exception as exc:
        logger.error(f"DEBUG: Erreur envoi touche {key}: {exc}")
        return {"error": str(exc)}

# Fonction de nettoyage pour fermer la connexion WebSocket
@app.on_event("shutdown")
async def shutdown_event():
    global _tv_controller
    if _tv_controller:
        logger.info("Fermeture du contrôleur TV")
        await _tv_controller.close()
        _tv_controller = None
