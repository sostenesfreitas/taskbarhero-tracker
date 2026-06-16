import re
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

PADRAO = re.compile(r"GetBoxCount Success Count : (\d+) // ItemKey : (\d+)")


class LogReader:
    """Lógica pura de tail (sem Qt): guarda offset, lê só bytes novos."""

    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self._offset = 0

    def seek_to_end(self) -> None:
        try:
            self._offset = self.caminho.stat().st_size
        except OSError:
            self._offset = 0

    def ler_novos(self) -> list:
        """ItemKeys das linhas acrescentadas desde a última leitura."""
        try:
            tamanho = self.caminho.stat().st_size
        except OSError:
            return []
        if tamanho < self._offset:   # truncado/rotacionado
            self._offset = 0
        if tamanho == self._offset:
            return []
        with self.caminho.open("rb") as f:
            f.seek(self._offset)
            trecho = f.read().decode("utf-8", "ignore")
            self._offset = tamanho
        return [m.group(2) for m in PADRAO.finditer(trecho)]


class LogWatcher(QObject):
    """Embrulho Qt: chama LogReader.ler_novos() num QTimer e emite sinal por ItemKey."""

    bau_detectado = Signal(str)   # item_key

    def __init__(self, caminho, intervalo_seg: int = 5, parent=None):
        super().__init__(parent)
        self._reader = LogReader(caminho)
        self._timer = QTimer(self)
        self._timer.setInterval(intervalo_seg * 1000)
        self._timer.timeout.connect(self._tick)

    def iniciar(self) -> None:
        self._reader.seek_to_end()
        self._timer.start()

    def parar(self) -> None:
        self._timer.stop()

    def definir_caminho(self, caminho) -> None:
        self._reader = LogReader(caminho)
        if self._timer.isActive():
            self._reader.seek_to_end()

    def definir_intervalo(self, intervalo_seg: int) -> None:
        self._timer.setInterval(intervalo_seg * 1000)

    def _tick(self) -> None:
        for item_key in self._reader.ler_novos():
            self.bau_detectado.emit(item_key)
