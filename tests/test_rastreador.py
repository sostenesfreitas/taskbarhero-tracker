from datetime import datetime, timedelta
from rastreador import Rastreador

def make_relogio(inicio):
    estado = {"agora": inicio}
    return estado, (lambda: estado["agora"])

def test_deteccao_entra_em_cooldown():
    estado, relogio = make_relogio(datetime(2026, 6, 16, 12, 0, 0))
    r = Rastreador(["910651"], relogio=relogio)  # cinza, cooldown 300s
    r.detectado("910651")
    e = r.estado("910651")
    assert e.estado == "cooldown"
    assert e.restante_seg == 300

def test_fica_pronto_apos_cooldown_e_emite_uma_vez():
    estado, relogio = make_relogio(datetime(2026, 6, 16, 12, 0, 0))
    r = Rastreador(["910651"], relogio=relogio)
    prontos = []
    r.on_pronto(lambda ik: prontos.append(ik))
    r.detectado("910651")
    estado["agora"] += timedelta(seconds=299)
    r.tick()
    assert prontos == [] and r.estado("910651").estado == "cooldown"
    estado["agora"] += timedelta(seconds=2)   # 301s total
    r.tick()
    assert prontos == ["910651"] and r.estado("910651").estado == "pronto"
    r.tick()   # não re-emite
    assert prontos == ["910651"]

def test_ignora_item_nao_monitorado():
    estado, relogio = make_relogio(datetime(2026, 6, 16, 12, 0, 0))
    r = Rastreador(["910651"], relogio=relogio)
    r.detectado("999999")
    assert r.estado("999999") is None

def test_redeteccao_reinicia_cooldown():
    estado, relogio = make_relogio(datetime(2026, 6, 16, 12, 0, 0))
    r = Rastreador(["920651"], relogio=relogio)  # azul, 420s
    r.detectado("920651")
    estado["agora"] += timedelta(seconds=500)
    r.tick()
    assert r.estado("920651").estado == "pronto"
    r.detectado("920651")
    assert r.estado("920651").estado == "cooldown"
    assert r.estado("920651").restante_seg == 420

def test_estado_inicial_nunca():
    estado, relogio = make_relogio(datetime(2026, 6, 16, 12, 0, 0))
    r = Rastreador(["910651"], relogio=relogio)
    assert r.estado("910651").estado == "nunca"
    assert r.estado("910651").restante_seg == 0
