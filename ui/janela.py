# ui/janela.py
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QEvent, QTimer, Signal
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

        self._moldura = QFrame(); self._moldura.setObjectName("Moldura")
        raiz = QVBoxLayout(self); raiz.setContentsMargins(0, 0, 0, 0); raiz.addWidget(self._moldura)
        col = QVBoxLayout(self._moldura); col.setContentsMargins(4, 4, 4, 4); col.setSpacing(3)

        self._titulobarra = self._construir_titulo()
        col.addWidget(self._titulobarra)
        self._status = QLabel(); self._status.setObjectName("Status")
        col.addWidget(self._status)
        self.atualizar_status()

        self._area = QScrollArea(); self._area.setWidgetResizable(True); self._area.setFrameShape(QFrame.NoFrame)
        self._area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget(); self._grade = QVBoxLayout(host)
        self._grade.setSpacing(0); self._grade.setContentsMargins(0, 0, 0, 0)
        self._area.setWidget(host); col.addWidget(self._area)
        self._popular_cards()

        self.setMinimumWidth(300)
        self._aplicar_estado_foco()
        self._ajustar_altura()
        self._rastreador.on_pronto(self._ao_ficar_pronto)

    def _construir_titulo(self) -> QFrame:
        barra = QFrame(); barra.setObjectName("TituloBarra")
        h = QHBoxLayout(barra); h.setContentsMargins(8, 4, 4, 4)
        titulo = QLabel("RECORDS"); titulo.setObjectName("TituloTexto")
        h.addWidget(titulo); h.addStretch()
        cfgbtn = QPushButton("⚙"); cfgbtn.setObjectName("BtnTitulo")  # ⚙
        cfgbtn.setFixedSize(22, 22); cfgbtn.setToolTip("Configurações")
        cfgbtn.clicked.connect(self._abrir_config)
        h.addWidget(cfgbtn)
        fechar = QPushButton("✕"); fechar.setObjectName("BtnTitulo")  # ✕
        fechar.setFixedSize(22, 22); fechar.setToolTip("Fechar")
        fechar.clicked.connect(self._fechar)
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

    def atualizar_status(self) -> None:
        """Reflete se o Player.log foi encontrado (erro de config mais comum)."""
        if Path(self._config.log_path).exists():
            self._status.setText("● Monitorando")
            self._status.setProperty("erro", "false")
        else:
            self._status.setText("⚠ Log não encontrado — abra ⚙ para escolher o arquivo")
            self._status.setProperty("erro", "true")
        self._atualizar_visibilidade_status()

    def _atualizar_visibilidade_status(self) -> None:
        """Sem foco mostra só a lista: o "Monitorando" some, mas o aviso de erro fica
        (senão o painel some sem explicação)."""
        erro = self._status.property("erro") == "true"
        self._status.setVisible(self.isActiveWindow() or erro)

    def recriar_cards(self) -> None:
        for card in self._cards.values():
            card.setParent(None)
        self._cards.clear()
        self._popular_cards()
        self._ajustar_altura()

    def _ajustar_altura(self) -> None:
        """Encolhe a janela para caber exatamente os baús (sem espaço sobrando).
        Diferido pro próximo ciclo: o sizeHint só fica correto após o layout assentar."""
        QTimer.singleShot(0, self._fazer_ajuste_altura)

    def _fazer_ajuste_altura(self) -> None:
        host = self._area.widget()
        host.adjustSize()
        altura = host.sizeHint().height()
        MAX = 420  # acima disso, rola
        self._area.setFixedHeight(min(altura, MAX))
        # adjustSize() não encolhe uma top-level já visível (quirk do Qt): força o resize
        # pelo sizeHint pra janela colar exatamente nos baús, sem sobra embaixo.
        self.layout().activate()
        self._moldura.layout().activate()
        self.resize(self.sizeHint())

    def _aplicar_estado_foco(self) -> None:
        """Sem foco: esconde o header e a moldura dourada (fica só a lista discreta)."""
        ativo = self.isActiveWindow()
        self._titulobarra.setVisible(ativo)   # header some quando sem foco
        self._atualizar_visibilidade_status()  # "Monitorando" some junto (só a lista fica)
        self._moldura.setProperty("ativo", "true" if ativo else "false")
        self._moldura.style().unpolish(self._moldura); self._moldura.style().polish(self._moldura)
        self._ajustar_altura()                # janela encolhe sem o header

    def changeEvent(self, ev):
        if ev.type() == QEvent.ActivationChange:
            self._aplicar_estado_foco()
        super().changeEvent(ev)

    def _ao_ficar_pronto(self, item_key: str) -> None:
        estado = self._rastreador.estado(item_key)
        if estado is None:
            return  # baú não é mais monitorado (ex.: removido via config)
        card = self._cards.get(item_key)
        if card:
            card.atualizar(); card.pulsar()
        if self._alertas:
            self._alertas.tocar(estado.bau.tipo)

    def contar_cards(self) -> int:
        return len(self._cards)

    def _abrir_config(self) -> None:
        from ui.painel_config import PainelConfig
        dlg = PainelConfig(self._config, self)
        if dlg.exec():
            dlg.aplicar()
            self.config_alterada.emit()

    def _fechar(self) -> None:
        self._config.janela_pos = [self.x(), self.y()]
        self._config.salvar()
        self.close()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.raise_(); self.activateWindow()   # reativa o foco -> header reaparece
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, ev):
        if self._drag_offset is not None and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, ev):
        self._drag_offset = None
