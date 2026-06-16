import pytest
from catalogo import (parse_item_key, bau_para_item_key, CATALOGO_PADRAO, STAGE_POR_NIVEL,
                      montar_item_key, baus_conhecidos, NIVEIS_CONHECIDOS)

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

def test_lv40_pesadelo():
    bau = bau_para_item_key("910401")
    assert bau.nivel == 40
    assert bau.stage_dificuldade == "Pesadelo"
    assert bau.stage_range == "1-9"

def test_niveis_baixos_tem_stage():
    assert STAGE_POR_NIVEL[1] == ("Normal", "1-1")
    assert STAGE_POR_NIVEL[15] == ("Normal", "2-3")
    assert STAGE_POR_NIVEL[30] == ("Normal", "3-8")
    b = bau_para_item_key("910151")   # cinza Lv15
    assert b.nivel == 15 and b.stage_dificuldade == "Normal" and b.stage_range == "2-3"

def test_montar_item_key():
    assert montar_item_key("cinza", 65) == "910651"
    assert montar_item_key("azul", 50) == "920501"
    assert montar_item_key("cinza", 1) == "910011"
    assert montar_item_key("cinza", 15) == "910151"
    # round-trip: monta e parseia de volta
    assert parse_item_key(montar_item_key("azul", 80))["nivel"] == 80

def test_baus_conhecidos_cobre_todos_niveis():
    chaves = baus_conhecidos()
    assert len(chaves) == len(NIVEIS_CONHECIDOS) * 2  # cinza + azul por nível
    assert "910011" in chaves and "920801" in chaves   # Lv1 cinza e Lv80 azul
    # todos parseiam sem erro
    for k in chaves:
        parse_item_key(k)

def test_vermelho_resolve_epico_e_icone():
    bau = bau_para_item_key("930801")
    assert bau.tipo == "vermelho"
    assert bau.raridade == "epico"
    assert bau.cooldown_seg == 420
    assert bau.icone == "Item_930011.png"
    assert bau.nome == "Act Boss Box Lv80"
