from log_watcher import LogReader

LINHA = "GetBoxCount Success Count : 1 // ItemKey : {}\n"

def test_seek_to_end_ignora_historico(tmp_path):
    p = tmp_path / "Player.log"
    p.write_text(LINHA.format("910651") + LINHA.format("920651"), encoding="utf-8")
    r = LogReader(p)
    r.seek_to_end()
    assert r.ler_novos() == []

def test_detecta_linhas_novas(tmp_path):
    p = tmp_path / "Player.log"
    p.write_text("ruído inicial\n", encoding="utf-8")
    r = LogReader(p)
    r.seek_to_end()
    with p.open("a", encoding="utf-8") as f:
        f.write(LINHA.format("910651"))
        f.write("linha irrelevante\n")
        f.write(LINHA.format("920801"))
    assert r.ler_novos() == ["910651", "920801"]

def test_arquivo_inexistente_retorna_vazio(tmp_path):
    r = LogReader(tmp_path / "naoexiste.log")
    assert r.ler_novos() == []

def test_seek_to_end_arquivo_inexistente_offset_zero(tmp_path):
    p = tmp_path / "Player.log"
    r = LogReader(p)
    r.seek_to_end()          # arquivo ainda não existe -> offset 0
    p.write_text(LINHA.format("910651"), encoding="utf-8")
    assert r.ler_novos() == ["910651"]

def test_truncamento_reabre_do_inicio(tmp_path):
    p = tmp_path / "Player.log"
    p.write_text(LINHA.format("910651") * 3, encoding="utf-8")
    r = LogReader(p)
    r.seek_to_end()
    p.write_text(LINHA.format("920651"), encoding="utf-8")
    assert r.ler_novos() == ["920651"]
