import json
import os
from pathlib import Path
from catalogo import CATALOGO_PADRAO


def log_path_padrao() -> str:
    base = os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\TesseractStudio\TaskbarHero")
    return str(Path(base) / "Player.log")


DEFAULTS = {
    "log_path": log_path_padrao(),
    "intervalo_seg": 5,
    "monitorados": list(CATALOGO_PADRAO),
    "som_cinza": True,
    "som_azul": True,
    "volume": 40,
    "janela_pos": [80, 80],
    "stages_custom": {},
}


class Config:
    def __init__(self, caminho=None):
        self.caminho = Path(caminho) if caminho else _config_path_padrao()
        dados = self._carregar()
        for chave, padrao in DEFAULTS.items():
            setattr(self, chave, dados.get(chave, padrao))

    def _carregar(self) -> dict:
        if not self.caminho.exists():
            return {}
        try:
            return json.loads(self.caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            try:
                self.caminho.replace(self.caminho.with_suffix(self.caminho.suffix + ".bak"))
            except OSError:
                pass
            return {}

    def salvar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = {chave: getattr(self, chave) for chave in DEFAULTS}
        self.caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def _config_path_padrao() -> Path:
    base = os.path.expandvars(r"%APPDATA%\TaskBarHeroTracker")
    return Path(base) / "config.json"
