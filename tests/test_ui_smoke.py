import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # roda sem display

@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication
    a = QApplication.instance() or QApplication([])
    yield a

def test_janela_instancia_com_cards(app, tmp_path):
    from config import Config
    from rastreador import Rastreador
    from ui.janela import Janela
    cfg = Config(tmp_path / "config.json")
    cfg.monitorados = ["910651", "920651"]
    rast = Rastreador(cfg.monitorados)
    janela = Janela(cfg, rast, alertas=None)
    assert janela.contar_cards() == 2

def test_carregar_fontes_nao_quebra(app):
    from ui.janela import carregar_fontes
    carregar_fontes()  # não deve lançar mesmo se faltar .ttf
