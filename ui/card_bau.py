# ui/card_bau.py
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QGraphicsOpacityEffect)

from utils import asset_path

# nome curto por tipo (estilo compacto do jogo)
NOME_CURTO_POR_TIPO = {"cinza": "Box", "azul": "Boss", "vermelho": "ActBoss"}


def _pixmap_pixelado(arquivo: str, alvo_px: int = 18) -> QPixmap:
    p = QPixmap(asset_path(f"icones/{arquivo}"))
    if p.isNull():
        return p
    return p.scaledToHeight(alvo_px, Qt.FastTransformation)


def _mmss(segundos: int) -> str:
    m, s = divmod(max(0, int(segundos)), 60)
    return f"{m:02d}:{s:02d}"


def _nome_curto(bau) -> str:
    return f"{NOME_CURTO_POR_TIPO.get(bau.tipo, bau.tipo)} Lv{bau.nivel}"


class CardBau(QFrame):
    """Uma linha compacta: ícone · nome curto · stage · tempo. Fica verde quando pronto."""

    def __init__(self, estado, parent=None):
        super().__init__(parent)
        self.setObjectName("Linha")
        self._estado = estado
        bau = estado.bau

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(8)

        icone = QLabel()
        icone.setPixmap(_pixmap_pixelado(bau.icone))
        icone.setFixedWidth(20)
        layout.addWidget(icone)

        self._nome = QLabel(_nome_curto(bau)); self._nome.setObjectName("LinhaNome")
        self._nome.setFixedWidth(92)  # mono é mais largo; cabe "ActBoss Lv80"
        layout.addWidget(self._nome)

        self._stage = QLabel(); self._stage.setObjectName("LinhaStage")
        layout.addWidget(self._stage)

        layout.addStretch()

        self._tempo = QLabel(); self._tempo.setObjectName("LinhaTempo")
        self._tempo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._tempo.setMinimumWidth(54)  # cabe "PRONTO" sem cortar
        layout.addWidget(self._tempo)

        self.setProperty("raridade", bau.raridade)
        self.atualizar()

    def atualizar(self) -> None:
        e, bau = self._estado, self._estado.bau
        pronto = e.estado == "pronto"
        self.setProperty("pronto", "true" if pronto else "false")
        self._stage.setText(f"{bau.stage_dificuldade} {bau.stage_range}")
        if pronto:
            self._tempo.setText("PRONTO")
        elif e.estado == "cooldown":
            self._tempo.setText(_mmss(e.restante_seg))
        else:  # nunca
            self._tempo.setText("--:--")
        # re-aplica QSS dependente de propriedade dinâmica (linha verde quando pronto)
        self.style().unpolish(self); self.style().polish(self)

    def pulsar(self) -> None:
        """Animação curta ao ficar pronto."""
        efeito = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(efeito)
        anim = QPropertyAnimation(efeito, b"opacity", self)
        anim.setDuration(150); anim.setStartValue(0.3); anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._anim = anim
