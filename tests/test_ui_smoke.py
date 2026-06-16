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

def test_status_reflete_log_ausente_e_presente(app, tmp_path):
    from config import Config
    from rastreador import Rastreador
    from ui.janela import Janela
    cfg = Config(tmp_path / "config.json")
    cfg.monitorados = ["910651"]
    cfg.log_path = str(tmp_path / "naoexiste.log")
    janela = Janela(cfg, Rastreador(cfg.monitorados), alertas=None)
    assert "não encontrado" in janela._status.text().lower()
    log = tmp_path / "Player.log"; log.write_text("", encoding="utf-8")
    cfg.log_path = str(log)
    janela.atualizar_status()
    assert "monitorando" in janela._status.text().lower()

def test_painel_adicionar_sem_aplicar_nao_altera_config(app, tmp_path):
    from config import Config
    from ui.painel_config import PainelConfig
    cfg = Config(tmp_path / "config.json")
    cfg.monitorados = ["910651"]
    p = PainelConfig(cfg)
    p._novo.setText("930801")
    p._adicionar()                      # adiciona à edição local
    assert cfg.monitorados == ["910651"]   # config NÃO muda sem aplicar (Cancelar é seguro)
    p.aplicar()                         # agora persiste o estado da lista
    assert set(cfg.monitorados) == {"910651", "930801"}
