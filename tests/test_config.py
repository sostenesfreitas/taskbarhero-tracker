import json
from config import Config, DEFAULTS

def test_defaults_quando_arquivo_nao_existe(tmp_path):
    c = Config(tmp_path / "naoexiste.json")
    assert c.monitorados == DEFAULTS["monitorados"]
    assert c.volume == DEFAULTS["volume"]
    assert c.som_cinza is True and c.som_azul is True
    assert c.intervalo_seg == 5

def test_round_trip_save_load(tmp_path):
    p = tmp_path / "config.json"
    c = Config(p)
    c.volume = 70
    c.monitorados = ["910651", "920651"]
    c.janela_pos = [100, 200]
    c.salvar()
    c2 = Config(p)
    assert c2.volume == 70
    assert c2.monitorados == ["910651", "920651"]
    assert c2.janela_pos == [100, 200]

def test_json_corrompido_recria_padroes(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{ isto não é json", encoding="utf-8")
    c = Config(p)
    assert c.monitorados == DEFAULTS["monitorados"]
    assert (tmp_path / "config.json.bak").exists()

def test_default_monitorados_nao_compartilhado(tmp_path):
    c1 = Config(tmp_path / "a.json")
    c2 = Config(tmp_path / "b.json")
    c1.monitorados.append("999999")
    assert "999999" not in c2.monitorados
    assert "999999" not in DEFAULTS["monitorados"]

def test_auto_detect_log_path_formato():
    from config import log_path_padrao
    p = log_path_padrao()
    assert p.endswith("Player.log")
    assert "TesseractStudio" in p and "TaskbarHero" in p
