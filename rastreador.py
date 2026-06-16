"""Modelo de estado de cooldown dos baús monitorados. Sem Qt; relógio injetável."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from catalogo import bau_para_item_key


@dataclass
class EstadoBau:
    bau: object                       # Bau
    estado: str = "nunca"             # 'nunca' | 'cooldown' | 'pronto'
    ultimo_detectado: datetime | None = None
    libera_em: datetime | None = None
    restante_seg: int = 0


class Rastreador:
    def __init__(self, monitorados: list[str], relogio=datetime.now):
        self._relogio = relogio
        self._callbacks_pronto = []
        self._estados: dict[str, EstadoBau] = {}
        for ik in monitorados:
            self._estados[str(ik)] = EstadoBau(bau=bau_para_item_key(ik))

    def on_pronto(self, cb) -> None:
        self._callbacks_pronto.append(cb)

    def estado(self, item_key: str):
        return self._estados.get(str(item_key))

    def estados(self) -> list:
        return list(self._estados.values())

    def detectado(self, item_key: str) -> None:
        e = self._estados.get(str(item_key))
        if e is None:
            return  # não monitorado
        agora = self._relogio()
        e.ultimo_detectado = agora
        e.libera_em = agora + timedelta(seconds=e.bau.cooldown_seg)
        e.estado = "cooldown"
        e.restante_seg = e.bau.cooldown_seg

    def tick(self) -> None:
        agora = self._relogio()
        for e in self._estados.values():
            if e.estado != "cooldown" or e.libera_em is None:
                continue
            restante = (e.libera_em - agora).total_seconds()
            if restante <= 0:
                e.estado = "pronto"
                e.restante_seg = 0
                for cb in self._callbacks_pronto:
                    cb(e.bau.item_key)
            else:
                e.restante_seg = int(restante) + (1 if restante % 1 else 0)

    def definir_monitorados(self, monitorados: list[str]) -> None:
        novos = {}
        for ik in monitorados:
            ik = str(ik)
            novos[ik] = self._estados.get(ik, EstadoBau(bau=bau_para_item_key(ik)))
        self._estados = novos
