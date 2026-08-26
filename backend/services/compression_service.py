"""
Compression Service for Agent World

Ce service gère la compression et décompression des fichiers générés
par les agents. Il supporte les formats GZIP et ZIP.

US-058: Compression des fichiers générés pour économiser de l'espace
Épic 8: Performance et Scalabilité
"""

import gzip
import io
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union


class CompressionError(Exception):
    """Erreur liée à la compression/décompression des fichiers."""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        self.message = message
        self.file_path = file_path
        super().__init__(self.message)


class UnsupportedCompressionFormatError(CompressionError):
    """Format de compression non supporté."""
    pass


class CompressionService:
    """
    Service de compression/décompression de fichiers.
    
    Supporte les formats :
    - GZIP : Compression individuelle de fichiers
    - ZIP : Compression multiple de fichiers/dossiers
    
    Attributes:
        enabled: Active ou désactive la compression
        default_format: Format par défaut (gzip ou zip)
        compression_level: Niveau de compression (1-9 pour GZIP, 0-9 pour ZIP)
        keep_original: Conserver les fichiers originaux après compression
    """
    
    SUPPORTED_FORMATS = {"gzip", "gz", "zip"}
    
    def __init__(
        self,
        enabled: bool = True,
        default_format: str = "gzip",
        compression_level: int = 6,
        keep_original: bool = True,
        chunk_size: int = 8192,
    ):
        """
        Initialise le service de compression.
        
        Args:
            enabled: Active ou désactive la compression
            default_format: Format par défaut (gzip ou zip)
            compression_level: Niveau de compression (1-9)
            keep_original: Conserver les fichiers originaux
            chunk_size: Taille des chunks pour la lecture/écriture
        """
        self.enabled = enabled
        self.default_format = default_format.lower()
        self.compression_level = self._validate_compression_level(compression_level)
        self.keep_original = keep_original
        self.chunk_size = chunk_size
        
        if self.default_format not in self.SUPPORTED_FORMATS:
            raise UnsupportedCompressionFormatError(
                f"Format non supporté: {default_format}. "
                f"Formats supportés: {', '.join(self.SUPPORTED_FORMATS)}"
            )
    
    def _validate_compression_level(self, level: int) -> int:
        """Valide le niveau de compression."""
        if not isinstance(level, int) or level < 0 or level > 9:
            raise ValueError("Le niveau de compression doit être un entier entre 0 et 9")
        return level
    
    def _validate_format(self, fmt: str) -> str:
        """Valide le format de compression."""
        fmt = fmt.lower()
        if fmt not in self.SUPPORTED_FORMATS:
            raise UnsupportedCompressionFormatError(
                f"Format non supporté: {fmt}. "
                f"Formats supportés: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        return fmt
    
    def compress_file(
        self,
        source_path: Union[str, Path],
        dest_path: Optional[Union[str, Path]] = None,
        fmt: Optional[str] = None,
        level: Optional[int] = None,
    ) -> Path:
        """
        Compresse un fichier.
        
        Args:
            source_path: Chemin du fichier source
            dest_path: Chemin de destination (optionnel, généré si non fourni)
            fmt: Format de compression (gzip ou zip)
            level: Niveau de compression (override le niveau par défaut)
            
        Returns:
            Path: Chemin du fichier compressé
            
        Raises:
            CompressionError: Si la compression échoue
            FileNotFoundError: Si le fichier source n'existe pas
        """
        if not self.enabled:
            return Path(source_path)
        
        fmt = self._validate_format(fmt or self.default_format)
        source_path = Path(source_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Fichier source introuvable: {source_path}")
        
        if not dest_path:
            dest_path = self._generate_compressed_path(source_path, fmt)
        else:
            dest_path = Path(dest_path)
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        level = level if level is not None else self.compression_level
        
        try:
            if fmt in ("gzip", "gz"):
                self._compress_gzip(source_path, dest_path, level)
            elif fmt == "zip":
                self._compress_zip(source_path, dest_path, level)
            
            # Ne pas conserver l'original si configuré
            if not self.keep_original:
                source_path.unlink()
            
            return dest_path
            
        except Exception as e:
            # Nettoyer le fichier de destination en cas d'échec
            if dest_path.exists():
                dest_path.unlink()
            raise CompressionError(f"Échec de la compression: {e}", str(source_path)) from e
    
    def _compress_gzip(
        self,
        source_path: Path,
        dest_path: Path,
        level: int,
    ) -> None:
        """Compresse un fichier en GZIP."""
        with open(source_path, 'rb') as f_in:
            with gzip.open(dest_path, 'wb', compresslevel=level) as f_out:
                shutil.copyfileobj(f_in, f_out, length=self.chunk_size)
    
    def _compress_zip(
        self,
        source_path: Path,
        dest_path: Path,
        level: int,
    ) -> None:
        """Compresse un fichier en ZIP."""
        with zipfile.ZipFile(
            dest_path,
            'w',
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=level,
        ) as zipf:
            # Ajouter le fichier avec son nom original dans l'archive
            arcname = source_path.name
            zipf.write(source_path, arcname=arcname)
    
    def compress_directory(
        self,
        source_dir: Union[str, Path],
        dest_path: Optional[Union[str, Path]] = None,
        fmt: str = "zip",
        level: Optional[int] = None,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> Path:
        """
        Compresse un dossier entier.
        
        Args:
            source_dir: Chemin du dossier source
            dest_path: Chemin de destination (optionnel)
            fmt: Format de compression (zip uniquement pour les dossiers)
            level: Niveau de compression
            include_patterns: Patterns de fichiers à inclure
            exclude_patterns: Patterns de fichiers à exclure
            
        Returns:
            Path: Chemin du fichier compressé
            
        Raises:
            CompressionError: Si la compression échoue
            UnsupportedCompressionFormatError: Si le format n'est pas supporté pour les dossiers
        """
        if not self.enabled:
            return Path(source_dir)
        
        fmt = self._validate_format(fmt)
        source_dir = Path(source_dir)
        
        if fmt in ("gzip", "gz"):
            raise UnsupportedCompressionFormatError(
                "Le format GZIP ne supporte pas la compression de dossiers. "
                "Utilisez le format ZIP."
            )
        
        if not dest_path:
            dest_path = self._generate_compressed_path(source_dir, fmt)
        else:
            dest_path = Path(dest_path)
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        level = level if level is not None else self.compression_level
        
        try:
            with zipfile.ZipFile(
                dest_path,
                'w',
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=level,
            ) as zipf:
                self._add_directory_to_zip(
                    zipf,
                    source_dir,
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                )
            
            if not self.keep_original:
                shutil.rmtree(source_dir)
            
            return dest_path
            
        except Exception as e:
            if dest_path.exists():
                dest_path.unlink()
            raise CompressionError(f"Échec de la compression du dossier: {e}", str(source_dir)) from e
    
    def _add_directory_to_zip(
        self,
        zipf: zipfile.ZipFile,
        directory: Path,
        parent_arcname: str = "",
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> None:
        """Ajoute récursivement un dossier à une archive ZIP."""
        for item in directory.iterdir():
            item_path = directory / item.name
            arcname = f"{parent_arcname}/{item.name}" if parent_arcname else item.name
            
            # Appliquer les filtres
            if include_patterns:
                if not any(item.name.lower().endswith(ext.lower()) for ext in include_patterns):
                    continue
            
            if exclude_patterns:
                if any(item.name.lower().endswith(ext.lower()) for ext in exclude_patterns):
                    continue
            
            if item.is_dir():
                self._add_directory_to_zip(
                    zipf,
                    item_path,
                    parent_arcname=arcname,
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                )
            else:
                zipf.write(item_path, arcname=arcname)
    
    def decompress_file(
        self,
        source_path: Union[str, Path],
        dest_path: Optional[Union[str, Path]] = None,
        fmt: Optional[str] = None,
    ) -> Path:
        """
        Décompresse un fichier.
        
        Args:
            source_path: Chemin du fichier compressé
            dest_path: Chemin de destination (optionnel)
            fmt: Format de compression (autodétecté si non fourni)
            
        Returns:
            Path: Chemin du fichier/dossier décompressé
            
        Raises:
            CompressionError: Si la décompression échoue
            FileNotFoundError: Si le fichier source n'existe pas
            UnsupportedCompressionFormatError: Si le format n'est pas supporté
        """
        source_path = Path(source_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Fichier source introuvable: {source_path}")
        
        # Autodétecter le format si non fourni
        if not fmt:
            fmt = self._detect_format(source_path)
        else:
            fmt = self._validate_format(fmt)
        
        if not dest_path:
            dest_path = self._generate_decompressed_path(source_path, fmt)
        else:
            dest_path = Path(dest_path)
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if fmt in ("gzip", "gz"):
                return self._decompress_gzip(source_path, dest_path)
            elif fmt == "zip":
                return self._decompress_zip(source_path, dest_path)
            else:
                raise UnsupportedCompressionFormatError(f"Format non supporté: {fmt}")
                
        except Exception as e:
            # Nettoyer en cas d'échec
            if dest_path.exists():
                if dest_path.is_dir():
                    shutil.rmtree(dest_path)
                else:
                    dest_path.unlink()
            raise CompressionError(f"Échec de la décompression: {e}", str(source_path)) from e
    
    def _detect_format(self, path: Path) -> str:
        """Détecte automatiquement le format de compression."""
        suffix = path.suffix.lower()
        
        if suffix in (".gz", ".gzip"):
            return "gzip"
        elif suffix == ".zip":
            return "zip"
        else:
            raise UnsupportedCompressionFormatError(
                f"Format non détecté pour: {path}. "
                f"Formats supportés: .gz, .gzip, .zip"
            )
    
    def _decompress_gzip(
        self,
        source_path: Path,
        dest_path: Path,
    ) -> Path:
        """Décompresse un fichier GZIP."""
        with gzip.open(source_path, 'rb') as f_in:
            with open(dest_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out, length=self.chunk_size)
        return dest_path
    
    def _decompress_zip(
        self,
        source_path: Path,
        dest_path: Path,
    ) -> Path:
        """Décompresse une archive ZIP."""
        with zipfile.ZipFile(source_path, 'r') as zipf:
            zipf.extractall(dest_path)
        return dest_path
    
    def _generate_compressed_path(
        self,
        source_path: Path,
        fmt: str,
    ) -> Path:
        """Génère le chemin de destination pour un fichier compressé."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if fmt in ("gzip", "gz"):
            return source_path.parent / f"{source_path.stem}_{timestamp}.gz"
        elif fmt == "zip":
            if source_path.is_dir():
                return source_path.parent / f"{source_path.name}_{timestamp}.zip"
            else:
                return source_path.parent / f"{source_path.stem}_{timestamp}.zip"
        else:
            return source_path.parent / f"{source_path.stem}_{timestamp}"
    
    def _generate_decompressed_path(
        self,
        source_path: Path,
        fmt: str,
    ) -> Path:
        """Génère le chemin de destination pour un fichier décompressé."""
        if fmt in ("gzip", "gz"):
            # Retirer l'extension .gz
            stem = source_path.stem
            if stem.endswith(".gzip"):
                stem = stem[:-5]  # Retirer .gzip
            elif stem.endswith(".gz"):
                stem = stem[:-3]  # Retirer .gz
            return source_path.parent / stem
        elif fmt == "zip":
            # Créer un dossier avec le nom de l'archive sans extension
            return source_path.parent / source_path.stem
        else:
            return source_path.parent / source_path.stem
    
    def get_compression_stats(
        self,
        original_path: Union[str, Path],
        compressed_path: Union[str, Path],
    ) -> dict[str, Any]:
        """
        Retourne les statistiques de compression.
        
        Args:
            original_path: Chemin du fichier original
            compressed_path: Chemin du fichier compressé
            
        Returns:
            dict: Statistiques de compression
        """
        original_path = Path(original_path)
        compressed_path = Path(compressed_path)
        
        if not original_path.exists() or not compressed_path.exists():
            return {"error": "Un ou plusieurs fichiers introuvables"}
        
        original_size = original_path.stat().st_size
        compressed_size = compressed_path.stat().st_size
        ratio = compressed_size / original_size if original_size > 0 else 0
        saved_space = original_size - compressed_size
        saved_percent = (saved_space / original_size * 100) if original_size > 0 else 0
        
        return {
            "original_size_bytes": original_size,
            "original_size_human": self._format_size(original_size),
            "compressed_size_bytes": compressed_size,
            "compressed_size_human": self._format_size(compressed_size),
            "ratio": round(ratio, 4),
            "saved_bytes": saved_space,
            "saved_percent": round(saved_percent, 2),
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formate la taille en octets en une chaîne lisible."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def is_compressed(self, path: Union[str, Path]) -> bool:
        """Vérifie si un fichier est compressé."""
        path = Path(path)
        return path.suffix.lower() in (".gz", ".gzip", ".zip")
    
    def get_supported_formats(self) -> list[str]:
        """Retourne la liste des formats supportés."""
        return list(self.SUPPORTED_FORMATS)
