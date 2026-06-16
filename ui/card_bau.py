# ui/card_bau.py
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                               QProgressBar, QGraphicsOpacityEffect)

from utils import asset_path


def _pixmap_pixelado(arquivo: str, escala: int = 2) -> QPixmap:
    p = QPixmap(asset_path(f"icones/{arquivo}"))
    if p.isNull():
        return p
    return p.scaled(p.width() * escala, p.height() * escala,
                    Qt.KeepAspectRatio, Qt.FastTransformation)


def _mmss(segundos: int) -> str:
    m, s = divmod(max(0, int(segundos)), 60)
    return f"{m:02d}:{s:02d}"


class CardBau(QFrame):
    def __init__(self, estado, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._estado = estado
        bau = estado.bau

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        icone = QLabel()
        icone.setPixmap(_pixmap_pixelado(bau.icone, 2))
        icone.setFixedWidth(36)
        layout.addWidget(icone)

        col = QVBoxLayout()
        col.setSpacing(2)
        self._nome = QLabel(bau.nome)
        self._stage = QLabel(); self._stage.setObjectName("Stage")
        self._barra = QProgressBar(); self._barra.setMaximum(bau.cooldown_seg); self._barra.setTextVisible(False)
        self._barra.setFixedHeight(10)
        self._tempo = QLabel(); self._tempo.setObjectName("Tempo")
        col.addWidget(self._nome)
        col.addWidget(self._stage)
        col.addWidget(self._barra)
        col.addWidget(self._tempo)
        layout.addLayout(col)

        self.setProperty("raridade", bau.raridade)
        self.atualizar()

    def atualizar(self) -> None:
        e, bau = self._estado, self._estado.bau
        pronto = e.estado == "pronto"
        self.setProperty("pronto", "true" if pronto else "false")
        self._barra.setProperty("pronto", "true" if pronto else "false")
        if pronto:
            self._stage.setText(f"VÁ PARA: {bau.stage_dificuldade} {bau.stage_range}")
            self._tempo.setText("PRONTO")
            self._barra.setValue(bau.cooldown_seg)
        elif e.estado == "cooldown":
            self._stage.setText(f"{bau.stage_dificuldade} {bau.stage_range}")
            self._tempo.setText(_mmss(e.restante_seg))
            self._barra.setValue(bau.cooldown_seg - e.restante_seg)
        else:  # nunca
            self._stage.setText(f"{bau.stage_dificuldade} {bau.stage_range}")
            self._tempo.setText("--:--")
            self._barra.setValue(0)
        # re-aplica QSS dependente de propriedade dinâmica
        for w in (self, self._barra):
            w.style().unpolish(w); w.style().polish(w)

    def pulsar(self) -> None:
        """Animação curta ao ficar pronto."""
        efeito = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(efeito)
        anim = QPropertyAnimation(efeito, b"opacity", self)
        anim.setDuration(150); anim.setStartValue(0.3); anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._anim = anim
