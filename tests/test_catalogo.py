import pytest
from catalogo import parse_item_key, bau_para_item_key, CATALOGO_PADRAO, STAGE_POR_NIVEL

def test_parse_cinza_lv65():
    info = parse_item_key("910651")
    assert info["tipo"] == "cinza"
    assert info["nivel"] == 65
    assert info["cooldown_seg"] == 300

def test_parse_azul_lv80():
    info = parse_item_key("920801")
    assert info["tipo"] == "azul"
    assert info["nivel"] == 80
    assert info["cooldown_seg"] == 420

def test_parse_vermelho_lv50():
    info = parse_item_key("930501")
    assert info["tipo"] == "vermelho"
    assert info["nivel"] == 50

def test_parse_invalido_curto():
    with pytest.raises(ValueError):
        parse_item_key("123")

def test_parse_invalido_nao_digito():
    with pytest.raises(ValueError):
        parse_item_key("91ABC1")

def test_parse_invalido_prefixo_desconhecido():
    with pytest.raises(ValueError):
        parse_item_key("940501")

def test_stage_por_nivel():
    assert STAGE_POR_NIVEL[50] == ("Pesadelo", "3-5")
    assert STAGE_POR_NIVEL[65] == ("Inferno", "2-5")
    assert STAGE_POR_NIVEL[80] == ("Tormento", "1-3")

def test_bau_para_item_key_resolve_tudo():
    bau = bau_para_item_key("920651")
    assert bau.tipo == "azul"
    assert bau.nivel == 65
    assert bau.raridade == "raro"
    assert bau.stage_dificuldade == "Inferno"
    assert bau.stage_range == "2-5"
    assert bau.cooldown_seg == 420
    assert bau.nome == "Stage Boss Box Lv65"

def test_catalogo_padrao_tem_6_monitorados():
    assert set(CATALOGO_PADRAO) == {"910501","910651","910801","920501","920651","920801"}
