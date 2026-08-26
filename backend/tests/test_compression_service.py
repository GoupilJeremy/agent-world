"""
Tests for CompressionService

US-058: Compression des fichiers générés pour économiser de l'espace
Épic 8: Performance et Scalabilité
"""

import gzip
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest

from ..services.compression_service import (
    CompressionError,
    CompressionService,
    UnsupportedCompressionFormatError,
)


@pytest.fixture
def temp_dir():
    """Crée un dossier temporaire pour les tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def compression_service():
    """Crée une instance de CompressionService."""
    return CompressionService(
        enabled=True,
        default_format="gzip",
        compression_level=6,
        keep_original=True,
    )


@pytest.fixture
def disabled_compression_service():
    """Crée une instance de CompressionService désactivée."""
    return CompressionService(
        enabled=False,
        default_format="gzip",
        compression_level=6,
        keep_original=True,
    )


class TestCompressionServiceInit:
    """Tests pour l'initialisation du service."""

    def test_init_with_defaults(self):
        """Test l'initialisation avec les valeurs par défaut."""
        service = CompressionService()
        assert service.enabled is True
        assert service.default_format == "gzip"
        assert service.compression_level == 6
        assert service.keep_original is True
        assert service.chunk_size == 8192

    def test_init_with_custom_values(self):
        """Test l'initialisation avec des valeurs personnalisées."""
        service = CompressionService(
            enabled=False,
            default_format="zip",
            compression_level=9,
            keep_original=False,
            chunk_size=16384,
        )
        assert service.enabled is False
        assert service.default_format == "zip"
        assert service.compression_level == 9
        assert service.keep_original is False
        assert service.chunk_size == 16384

    def test_init_with_invalid_format(self):
        """Test l'initialisation avec un format invalide."""
        with pytest.raises(UnsupportedCompressionFormatError):
            CompressionService(default_format="invalid")

    def test_init_with_invalid_compression_level(self):
        """Test l'initialisation avec un niveau de compression invalide."""
        with pytest.raises(ValueError):
            CompressionService(compression_level=-1)

        with pytest.raises(ValueError):
            CompressionService(compression_level=10)

        with pytest.raises(ValueError):
            CompressionService(compression_level="invalid")


class TestCompressionServiceValidation:
    """Tests pour les méthodes de validation."""

    def test_validate_format_gzip(self, compression_service):
        """Test la validation du format gzip."""
        assert compression_service._validate_format("gzip") == "gzip"
        assert compression_service._validate_format("GZIP") == "gzip"
        assert compression_service._validate_format("gz") == "gz"

    def test_validate_format_zip(self, compression_service):
        """Test la validation du format zip."""
        assert compression_service._validate_format("zip") == "zip"
        assert compression_service._validate_format("ZIP") == "zip"

    def test_validate_format_invalid(self, compression_service):
        """Test la validation d'un format invalide."""
        with pytest.raises(UnsupportedCompressionFormatError):
            compression_service._validate_format("invalid")

    def test_get_supported_formats(self, compression_service):
        """Test la récupération des formats supportés."""
        formats = compression_service.get_supported_formats()
        assert "gzip" in formats
        assert "gz" in formats
        assert "zip" in formats


class TestCompressionServiceCompressFile:
    """Tests pour la compression de fichiers."""

    def test_compress_file_gzip(self, compression_service, temp_dir):
        """Test la compression d'un fichier en GZIP."""
        # Créer un fichier test
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!" * 100)

        # Compresser le fichier
        compressed_path = compression_service.compress_file(
            test_file, dest_path=temp_dir / "test.txt.gz", fmt="gzip"
        )

        assert compressed_path.exists()
        assert compressed_path.suffix == ".gz"
        assert test_file.exists()  # keep_original=True

        # Vérifier que le fichier est valide
        with gzip.open(compressed_path, "rt") as f:
            content = f.read()

        assert "Hello, World!" in content

    def test_compress_file_zip(self, compression_service, temp_dir):
        """Test la compression d'un fichier en ZIP."""
        # Créer un fichier test
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!" * 100)

        # Compresser le fichier
        compressed_path = compression_service.compress_file(
            test_file, dest_path=temp_dir / "test.zip", fmt="zip"
        )

        assert compressed_path.exists()
        assert compressed_path.suffix == ".zip"
        assert test_file.exists()  # keep_original=True

        # Vérifier que le fichier est valide
        with zipfile.ZipFile(compressed_path, "r") as zipf:
            assert "test.txt" in zipf.namelist()
            with zipf.open("test.txt") as f:
                content = f.read().decode("utf-8")
            assert "Hello, World!" in content

    def test_compress_file_without_dest(self, compression_service, temp_dir):
        """Test la compression avec génération automatique du chemin de destination."""
        # Créer un fichier test
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        # Compresser sans spécifier de destination
        compressed_path = compression_service.compress_file(test_file, fmt="gzip")

        assert compressed_path.exists()
        assert compressed_path.parent == test_file.parent
        assert ".gz" in compressed_path.name

    def test_compress_file_disabled(self, disabled_compression_service, temp_dir):
        """Test la compression quand le service est désactivé."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        # Quand désactivé, retourne le fichier original
        result = disabled_compression_service.compress_file(test_file)

        assert result == test_file

    def test_compress_file_nonexistent(self, compression_service, temp_dir):
        """Test la compression d'un fichier qui n'existe pas."""
        nonexistent_file = temp_dir / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            compression_service.compress_file(nonexistent_file)

    def test_compress_file_invalid_format(self, compression_service, temp_dir):
        """Test la compression avec un format invalide."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        with pytest.raises(UnsupportedCompressionFormatError):
            compression_service.compress_file(test_file, fmt="invalid")


class TestCompressionServiceDecompressFile:
    """Tests pour la décompression de fichiers."""

    def test_decompress_gzip_file(self, compression_service, temp_dir):
        """Test la décompression d'un fichier GZIP."""
        # Créer et compresser un fichier
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!" * 100)

        compressed_path = compression_service.compress_file(
            test_file, dest_path=temp_dir / "test.txt.gz", fmt="gzip"
        )

        # Décompresser le fichier
        decompressed_path = compression_service.decompress_file(
            compressed_path, dest_path=temp_dir / "test_decompressed.txt"
        )

        assert decompressed_path.exists()
        assert decompressed_path.read_text() == test_file.read_text()

    def test_decompress_zip_file(self, compression_service, temp_dir):
        """Test la décompression d'un fichier ZIP."""
        # Créer et compresser un fichier
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!" * 100)

        compressed_path = compression_service.compress_file(
            test_file, dest_path=temp_dir / "test.zip", fmt="zip"
        )

        # Décompresser le fichier
        decompressed_dir = compression_service.decompress_file(
            compressed_path, dest_path=temp_dir / "test_decompressed"
        )

        assert decompressed_dir.exists()
        assert (decompressed_dir / "test.txt").exists()

        with open(decompressed_dir / "test.txt", "r") as f:
            content = f.read()

        assert "Hello, World!" in content

    def test_decompress_autodetect_format(self, compression_service, temp_dir):
        """Test la détection automatique du format."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        # Compresser en GZIP
        compressed_path = compression_service.compress_file(
            test_file, dest_path=temp_dir / "test.txt.gz", fmt="gzip"
        )

        # Décompresser sans spécifier le format (doit auto-détecter)
        decompressed_path = compression_service.decompress_file(compressed_path)

        assert decompressed_path.exists()

    def test_decompress_nonexistent_file(self, compression_service, temp_dir):
        """Test la décompression d'un fichier qui n'existe pas."""
        nonexistent_file = temp_dir / "nonexistent.gz"

        with pytest.raises(FileNotFoundError):
            compression_service.decompress_file(nonexistent_file)


class TestCompressionServiceCompressDirectory:
    """Tests pour la compression de dossiers."""

    def test_compress_directory_zip(self, compression_service, temp_dir):
        """Test la compression d'un dossier en ZIP."""
        # Créer un dossier avec des fichiers
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1 content")
        (test_dir / "file2.txt").write_text("File 2 content")

        # Compresser le dossier
        compressed_path = compression_service.compress_directory(
            test_dir, dest_path=temp_dir / "test_dir.zip", fmt="zip"
        )

        assert compressed_path.exists()
        assert test_dir.exists()  # keep_original=True

        # Vérifier le contenu de l'archive
        with zipfile.ZipFile(compressed_path, "r") as zipf:
            assert "file1.txt" in zipf.namelist()
            assert "file2.txt" in zipf.namelist()

    def test_compress_directory_gzip_fails(self, compression_service, temp_dir):
        """Test que la compression d'un dossier en GZIP échoue."""
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("File 1 content")

        with pytest.raises(UnsupportedCompressionFormatError):
            compression_service.compress_directory(test_dir, fmt="gzip")


class TestCompressionServiceStats:
    """Tests pour les statistiques de compression."""

    def test_get_compression_stats(self, compression_service, temp_dir):
        """Test la récupération des statistiques de compression."""
        # Créer un fichier test
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!" * 1000)

        # Compresser le fichier
        compressed_path = compression_service.compress_file(
            test_file, dest_path=temp_dir / "test.txt.gz", fmt="gzip"
        )

        # Récupérer les statistiques
        stats = compression_service.get_compression_stats(test_file, compressed_path)

        assert "original_size_bytes" in stats
        assert "compressed_size_bytes" in stats
        assert "ratio" in stats
        assert "saved_bytes" in stats
        assert "saved_percent" in stats
        assert stats["original_size_bytes"] > stats["compressed_size_bytes"]
        assert stats["saved_percent"] > 0

    def test_get_compression_stats_nonexistent(self, compression_service, temp_dir):
        """Test les statistiques avec des fichiers qui n'existent pas."""
        nonexistent1 = temp_dir / "nonexistent1.txt"
        nonexistent2 = temp_dir / "nonexistent2.txt.gz"

        stats = compression_service.get_compression_stats(nonexistent1, nonexistent2)

        assert "error" in stats


class TestCompressionServiceUtilities:
    """Tests pour les méthodes utilitaires."""

    def test_is_compressed_gzip(self, compression_service, temp_dir):
        """Test la détection de fichiers compressés en GZIP."""
        gzip_file = temp_dir / "test.gz"
        gzip_file.write_text("test")

        assert compression_service.is_compressed(gzip_file) is True

    def test_is_compressed_zip(self, compression_service, temp_dir):
        """Test la détection de fichiers compressés en ZIP."""
        zip_file = temp_dir / "test.zip"
        zip_file.write_text("test")

        assert compression_service.is_compressed(zip_file) is True

    def test_is_compressed_not_compressed(self, compression_service, temp_dir):
        """Test la détection de fichiers non compressés."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("test")

        assert compression_service.is_compressed(txt_file) is False

    def test_format_size(self, compression_service):
        """Test le formatage de la taille."""
        assert compression_service._format_size(0) == "0.00 B"
        assert compression_service._format_size(100) == "100.00 B"
        assert compression_service._format_size(1024) == "1.00 KB"
        assert compression_service._format_size(1024 * 1024) == "1.00 MB"
        assert compression_service._format_size(1024 * 1024 * 1024) == "1.00 GB"


class TestCompressionServiceCleanup:
    """Tests pour le nettoyage après échec."""

    def test_cleanup_after_compression_failure(
        self, compression_service, temp_dir, mocker
    ):
        """Test le nettoyage après un échec de compression."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")
        dest_path = temp_dir / "test.txt.gz"

        # Simuler une erreur lors de l'écriture
        mocker.patch("builtins.open", side_effect=IOError("Write error"))

        with pytest.raises(CompressionError):
            compression_service.compress_file(test_file, dest_path=dest_path)

        # Le fichier de destination ne doit pas exister
        assert not dest_path.exists()
