"""Alertas sonoros: toca um som por tipo de baú quando ele fica pronto."""
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from utils import asset_path


class Alertas:
    """Toca som por tipo de baú, respeitando toggles e volume da config."""

    def __init__(self, config):
        self._config = config
        self._efeitos = {}
        for tipo, arq in (("cinza", "cinza.wav"), ("azul", "azul.wav")):
            caminho = asset_path(f"sons/{arq}")
            if Path(caminho).exists():
                ef = QSoundEffect()
                ef.setSource(QUrl.fromLocalFile(caminho))
                self._efeitos[tipo] = ef

    def tocar(self, tipo: str) -> None:
        ativo = {"cinza": self._config.som_cinza, "azul": self._config.som_azul}.get(tipo, True)
        if not ativo:
            return
        ef = self._efeitos.get(tipo)
        if ef is None:
            return  # arquivo ausente -> silêncio, sem crash
        ef.setVolume(max(0.0, min(1.0, self._config.volume / 100.0)))
        ef.play()
