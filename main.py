# main.py
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from config import Config
from rastreador import Rastreador
from log_watcher import LogWatcher
from alertas import Alertas
from theme import QSS
from utils import asset_path
from ui.janela import Janela, carregar_fontes


class App:
    def __init__(self):
        self.config = Config()
        self.rastreador = Rastreador(self.config.monitorados)
        self.alertas = Alertas(self.config)
        self.watcher = LogWatcher(self.config.log_path, self.config.intervalo_seg)
        self.watcher.bau_detectado.connect(self.rastreador.detectado)
        self.janela = Janela(self.config, self.rastreador, self.alertas)
        self.janela.config_alterada.connect(self._reconfigurar)

        self.ui_timer = QTimer()
        self.ui_timer.setInterval(1000)
        self.ui_timer.timeout.connect(self._tick)
        self.ui_timer.start()
        self.watcher.iniciar()

    def _tick(self):
        self.rastreador.tick()
        self.janela.atualizar_cards()

    def _reconfigurar(self):
        self.rastreador.definir_monitorados(self.config.monitorados)
        self.watcher.definir_intervalo(self.config.intervalo_seg)
        self.watcher.definir_caminho(self.config.log_path)
        self.janela.recriar_cards()
        self.janela.atualizar_status()

    def run(self):
        self.janela.show()


def main():
    app = QApplication(sys.argv)
    carregar_fontes()
    icone = asset_path("app.ico")
    if Path(icone).exists():
        app.setWindowIcon(QIcon(icone))
    app.setStyleSheet(QSS)
    a = App()
    a.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
