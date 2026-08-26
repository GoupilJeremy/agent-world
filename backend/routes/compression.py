"""
Compression Routes for Agent World

Endpoints pour la gestion de la compression/décompression des fichiers.

US-058: Compression des fichiers générés pour économiser de l'espace
Épic 8: Performance et Scalabilité
"""

import os
from flask import Blueprint, current_app, jsonify, request
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage

from ..services.compression_service import (
    CompressionError,
    CompressionService,
    UnsupportedCompressionFormatError,
)


# Créer le blueprint pour les routes de compression
compression_bp = Blueprint("compression", __name__, url_prefix="/api/compression")


class CompressionStatsResource(Resource):
    """Ressource pour obtenir les statistiques de compression."""
    
    def get(self):
        """Retourne les statistiques de compression."""
        try:
            compression_service: CompressionService = current_app.extensions["compression_service"]
            
            # Récupérer les paramètres de la requête
            parser = reqparse.RequestParser()
            parser.add_argument("original_path", type=str, required=True, help="Chemin du fichier original")
            parser.add_argument("compressed_path", type=str, required=True, help="Chemin du fichier compressé")
            args = parser.parse_args()
            
            stats = compression_service.get_compression_stats(
                args["original_path"],
                args["compressed_path"]
            )
            
            return {"success": True, "data": stats}, 200
            
        except FileNotFoundError as e:
            return {"success": False, "error": f"Fichier introuvable: {e}"}, 404
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des stats: {e}")
            return {"success": False, "error": str(e)}, 500


class CompressFileResource(Resource):
    """Ressource pour compresser un fichier."""
    
    def post(self):
        """Compresse un fichier téléversé."""
        try:
            compression_service: CompressionService = current_app.extensions["compression_service"]
            
            # Vérifier que le service est activé
            if not compression_service.enabled:
                return {"success": False, "error": "La compression est désactivée"}, 400
            
            # Récupérer le fichier de la requête
            if 'file' not in request.files:
                return {"success": False, "error": "Aucun fichier fourni"}, 400
            
            file = request.files['file']
            if file.filename == '':
                return {"success": False, "error": "Nom de fichier vide"}, 400
            
            # Récupérer les paramètres optionnels
            fmt = request.form.get('format', compression_service.default_format)
            level = request.form.get('level', None)
            if level:
                level = int(level)
            
            # Sauvegarder temporairement le fichier
            import tempfile
            from pathlib import Path
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / file.filename
                file.save(str(temp_path))
                
                # Compresser le fichier
                compressed_path = compression_service.compress_file(
                    temp_path,
                    fmt=fmt,
                    level=level
                )
                
                # Retourner le fichier compressé
                compressed_filename = compressed_path.name
                compressed_data = compressed_path.read_bytes()
                
                # Nettoyer
                compressed_path.unlink(missing_ok=True)
                
                return {
                    "success": True,
                    "data": {
                        "original_filename": file.filename,
                        "compressed_filename": compressed_filename,
                        "format": fmt,
                        "size": len(compressed_data)
                    }
                }, 200
                
        except UnsupportedCompressionFormatError as e:
            return {"success": False, "error": f"Format non supporté: {e}"}, 400
        except CompressionError as e:
            return {"success": False, "error": f"Erreur de compression: {e}"}, 500
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la compression: {e}")
            return {"success": False, "error": str(e)}, 500


class DecompressFileResource(Resource):
    """Ressource pour décompresser un fichier."""
    
    def post(self):
        """Décompresse un fichier téléversé."""
        try:
            compression_service: CompressionService = current_app.extensions["compression_service"]
            
            # Vérifier que le service est activé
            if not compression_service.enabled:
                return {"success": False, "error": "La compression est désactivée"}, 400
            
            # Récupérer le fichier de la requête
            if 'file' not in request.files:
                return {"success": False, "error": "Aucun fichier fourni"}, 400
            
            file = request.files['file']
            if file.filename == '':
                return {"success": False, "error": "Nom de fichier vide"}, 400
            
            # Vérifier que le fichier est compressé
            if not compression_service.is_compressed(file.filename):
                return {"success": False, "error": "Le fichier n'est pas compressé"}, 400
            
            # Récupérer le format de la requête ou par détection
            fmt = request.form.get('format', None)
            
            # Sauvegarder temporairement le fichier
            import tempfile
            from pathlib import Path
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / file.filename
                file.save(str(temp_path))
                
                # Décompresser le fichier
                decompressed_path = compression_service.decompress_file(
                    temp_path,
                    fmt=fmt
                )
                
                # Retourner le fichier décompressé
                if decompressed_path.is_dir():
                    # Pour les archives ZIP, retourner la liste des fichiers
                    files_list = [f.name for f in decompressed_path.iterdir() if f.is_file()]
                    return {
                        "success": True,
                        "data": {
                            "archive_filename": file.filename,
                            "extracted_files": files_list,
                            "count": len(files_list)
                        }
                    }, 200
                else:
                    # Pour les fichiers simples, retourner le contenu
                    decompressed_data = decompressed_path.read_bytes()
                    return {
                        "success": True,
                        "data": {
                            "original_filename": file.filename,
                            "decompressed_filename": decompressed_path.name,
                            "size": len(decompressed_data)
                        }
                    }, 200
                
        except UnsupportedCompressionFormatError as e:
            return {"success": False, "error": f"Format non supporté: {e}"}, 400
        except CompressionError as e:
            return {"success": False, "error": f"Erreur de décompression: {e}"}, 500
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la décompression: {e}")
            return {"success": False, "error": str(e)}, 500


class CompressionInfoResource(Resource):
    """Ressource pour obtenir des informations sur le service de compression."""
    
    def get(self):
        """Retourne les informations de configuration du service de compression."""
        try:
            compression_service: CompressionService = current_app.extensions["compression_service"]
            
            return {
                "success": True,
                "data": {
                    "enabled": compression_service.enabled,
                    "default_format": compression_service.default_format,
                    "compression_level": compression_service.compression_level,
                    "keep_original": compression_service.keep_original,
                    "supported_formats": compression_service.get_supported_formats()
                }
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération de la configuration: {e}")
            return {"success": False, "error": str(e)}, 500


class CheckCompressionResource(Resource):
    """Ressource pour vérifier si un fichier est compressé."""
    
    def get(self):
        """Vérifie si un fichier est compressé."""
        try:
            compression_service: CompressionService = current_app.extensions["compression_service"]
            
            parser = reqparse.RequestParser()
            parser.add_argument("path", type=str, required=True, help="Chemin du fichier à vérifier")
            args = parser.parse_args()
            
            is_compressed = compression_service.is_compressed(args["path"])
            
            return {
                "success": True,
                "data": {
                    "path": args["path"],
                    "is_compressed": is_compressed
                }
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la vérification: {e}")
            return {"success": False, "error": str(e)}, 500


def register_compression_resources(api):
    """Enregistre les ressources de compression sur l'API."""
    api.add_resource(CompressionStatsResource, "/compression/stats")
    api.add_resource(CompressFileResource, "/compression/compress")
    api.add_resource(DecompressFileResource, "/compression/decompress")
    api.add_resource(CompressionInfoResource, "/compression/info")
    api.add_resource(CheckCompressionResource, "/compression/check")
