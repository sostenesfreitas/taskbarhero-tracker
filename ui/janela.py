# ui/janela.py
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea)

from utils import asset_path
from ui.card_bau import CardBau


def carregar_fontes() -> None:
    for arq in ("PressStart2P-Regular.ttf", "PixelifySans-Regular.ttf", "DepartureMono-Regular.otf"):
        try:
            QFontDatabase.addApplicationFont(asset_path(f"fonts/{arq}"))
        except Exception:
            pass  # fonte ausente -> fallback do sistema


class Janela(QWidget):
    config_alterada = Signal()

    def __init__(self, config, rastreador, alertas=None, parent=None):
        super().__init__(parent)
        self._config = config
        self._rastreador = rastreador
        self._alertas = alertas
        self._cards = {}
        self._drag_offset = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.move(QPoint(*config.janela_pos))

        moldura = QFrame(); moldura.setObjectName("Moldura")
        raiz = QVBoxLayout(self); raiz.setContentsMargins(0, 0, 0, 0); raiz.addWidget(moldura)
        col = QVBoxLayout(moldura); col.setContentsMargins(6, 6, 6, 6); col.setSpacing(6)

        col.addWidget(self._construir_titulo())
        self._status = QLabel("● Monitorando"); self._status.setObjectName("Status")
        col.addWidget(self._status)

        area = QScrollArea(); area.setWidgetResizable(True); area.setFrameShape(QFrame.NoFrame)
        host = QWidget(); self._grade = QVBoxLayout(host); self._grade.setSpacing(6)
        area.setWidget(host); col.addWidget(area)
        self._popular_cards()

        self.setMinimumWidth(300)
        self._rastreador.on_pronto(self._ao_ficar_pronto)

    def _construir_titulo(self) -> QFrame:
        barra = QFrame(); barra.setObjectName("TituloBarra")
        h = QHBoxLayout(barra); h.setContentsMargins(8, 4, 4, 4)
        titulo = QLabel("TASKBAR HERO"); titulo.setObjectName("TituloTexto")
        h.addWidget(titulo); h.addStretch()
        fechar = QPushButton("X"); fechar.setFixedSize(24, 24); fechar.clicked.connect(self._fechar)
        h.addWidget(fechar)
        return barra

    def _popular_cards(self) -> None:
        def chave(e):
            return (0 if e.estado == "pronto" else 1, e.restante_seg, e.bau.nivel)
        for e in sorted(self._rastreador.estados(), key=chave):
            card = CardBau(e)
            self._cards[e.bau.item_key] = card
            self._grade.addWidget(card)

    def atualizar_cards(self) -> None:
        for card in self._cards.values():
            card.atualizar()

    def recriar_cards(self) -> None:
        for card in self._cards.values():
            card.setParent(None)
        self._cards.clear()
        self._popular_cards()

    def _ao_ficar_pronto(self, item_key: str) -> None:
        card = self._cards.get(item_key)
        if card:
            card.atualizar(); card.pulsar()
        if self._alertas:
            tipo = self._rastreador.estado(item_key).bau.tipo
            self._alertas.tocar(tipo)

    def contar_cards(self) -> int:
        return len(self._cards)

    def _fechar(self) -> None:
        self._config.janela_pos = [self.x(), self.y()]
        self._config.salvar()
        self.close()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, ev):
        if self._drag_offset is not None and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, ev):
        self._drag_offset = None
