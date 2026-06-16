"""Acompanha o Player.log e reporta novos drops de baú. Núcleo (LogReader) sem Qt."""
import re
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

# o count vira grupo não-capturante; o único grupo capturado (group 1) é o ItemKey.
PADRAO = re.compile(r"GetBoxCount Success Count : (?:\d+) // ItemKey : (\d+)")


class LogReader:
    """Lógica pura de tail (sem Qt): guarda offset, lê só bytes novos.

    Usa modo binário de propósito: precisamos dar seek() para um offset de byte
    arbitrário (stat().st_size), o que só é garantido em arquivos binários — em
    modo texto, seeks válidos são apenas 0 ou um valor retornado por tell().
    As linhas de drop são ASCII, então decode utf-8/ignore é seguro.
    """

    def __init__(self, caminho: Path | str):
        self.caminho = Path(caminho)
        self._offset = 0

    def seek_to_end(self) -> None:
        try:
            self._offset = self.caminho.stat().st_size
        except OSError:
            self._offset = 0

    def ler_novos(self) -> list[str]:
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
        return [m.group(1) for m in PADRAO.finditer(trecho)]


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

    def definir_caminho(self, caminho: Path | str) -> None:
        self._reader = LogReader(caminho)
        if self._timer.isActive():
            self._reader.seek_to_end()

    def definir_intervalo(self, intervalo_seg: int) -> None:
        self._timer.setInterval(intervalo_seg * 1000)
        if self._timer.isActive():
            self._timer.start()  # re-arma com o novo intervalo imediatamente

    def _tick(self) -> None:
        for item_key in self._reader.ler_novos():
            self.bau_detectado.emit(item_key)
