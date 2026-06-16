from datetime import datetime, timedelta
from log_watcher import LogReader
from rastreador import Rastreador

LINHA = "GetBoxCount Success Count : 1 // ItemKey : {}\n"

def test_pipeline_log_ate_pronto(tmp_path):
    log = tmp_path / "Player.log"
    log.write_text("linha de histórico ignorada\n", encoding="utf-8")

    # relógio injetável
    estado = {"agora": datetime(2026, 6, 16, 12, 0, 0)}
    relogio = lambda: estado["agora"]

    reader = LogReader(log)
    reader.seek_to_end()                       # ignora histórico
    rast = Rastreador(["910651", "920651"], relogio=relogio)  # cinza 300s, azul 420s
    prontos = []
    rast.on_pronto(lambda ik: prontos.append(ik))

    # o jogo dropa dois baús
    with log.open("a", encoding="utf-8") as f:
        f.write(LINHA.format("910651"))
        f.write(LINHA.format("920651"))

    # o "watcher tick": lê o log e alimenta o rastreador
    for ik in reader.ler_novos():
        rast.detectado(ik)
    assert rast.estado("910651").estado == "cooldown"
    assert rast.estado("920651").estado == "cooldown"

    # passa 301s: o cinza (300s) libera, o azul (420s) ainda não
    estado["agora"] += timedelta(seconds=301)
    rast.tick()
    assert prontos == ["910651"]
    assert rast.estado("910651").estado == "pronto"
    assert rast.estado("920651").estado == "cooldown"

    # passa até 421s totais: o azul libera
    estado["agora"] += timedelta(seconds=120)   # 421s total
    rast.tick()
    assert prontos == ["910651", "920651"]
    assert rast.estado("920651").estado == "pronto"

def test_pipeline_redrop_apos_pronto(tmp_path):
    log = tmp_path / "Player.log"
    log.write_text("", encoding="utf-8")
    estado = {"agora": datetime(2026, 6, 16, 12, 0, 0)}
    relogio = lambda: estado["agora"]
    reader = LogReader(log); reader.seek_to_end()
    rast = Rastreador(["910651"], relogio=relogio)

    with log.open("a", encoding="utf-8") as f:
        f.write(LINHA.format("910651"))
    for ik in reader.ler_novos():
        rast.detectado(ik)
    estado["agora"] += timedelta(seconds=301)
    rast.tick()
    assert rast.estado("910651").estado == "pronto"

    # dropa de novo -> volta pra cooldown
    with log.open("a", encoding="utf-8") as f:
        f.write(LINHA.format("910651"))
    for ik in reader.ler_novos():
        rast.detectado(ik)
    assert rast.estado("910651").estado == "cooldown"
