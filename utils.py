"""Utilitários compartilhados."""
import sys
from pathlib import Path


def asset_path(rel: str) -> str:
    """Caminho de um asset, funcionando em dev e empacotado (PyInstaller _MEIPASS)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return str(base / "assets" / rel)
