# ui/painel_config.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                               QSlider, QSpinBox, QListWidget, QListWidgetItem, QPushButton,
                               QLineEdit, QFileDialog, QComboBox)
from PySide6.QtCore import Qt

from catalogo import bau_para_item_key, parse_item_key, baus_conhecidos
from theme import C


class PainelConfig(QDialog):
    """Edita config: baús monitorados, sons, volume, intervalo, caminho do log."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        # lista de edição local: alterações só vão pro config em aplicar() (Cancelar não afeta)
        self._monitorados_em_edicao = list(config.monitorados)
        self.setWindowTitle("Configurações")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Baús monitorados:"))
        self._lista = QListWidget()
        self._recarregar_lista()
        lay.addWidget(self._lista)

        # menu de baús conhecidos (do mais fraco ao mais forte) — fácil para quem não sabe o ItemKey
        conhecidorow = QHBoxLayout()
        self._combo = QComboBox()
        for ik in baus_conhecidos():
            b = bau_para_item_key(ik)
            self._combo.addItem(f"{b.nome}  |  {b.stage_dificuldade} {b.stage_range}", ik)
        btn_conhecido = QPushButton("Adicionar"); btn_conhecido.clicked.connect(self._adicionar_conhecido)
        conhecidorow.addWidget(self._combo, 1); conhecidorow.addWidget(btn_conhecido)
        lay.addWidget(QLabel("Adicionar baú:"))
        lay.addLayout(conhecidorow)

        # entrada manual por ItemKey (avançado: Act Boss, baús fora da lista)
        addrow = QHBoxLayout()
        self._novo = QLineEdit(); self._novo.setPlaceholderText("ou ItemKey manual (ex.: 930801)")
        btn_add = QPushButton("Adicionar"); btn_add.clicked.connect(self._adicionar)
        addrow.addWidget(self._novo); addrow.addWidget(btn_add)
        lay.addLayout(addrow)

        self._som_cinza = QCheckBox("Som baú cinza"); self._som_cinza.setChecked(config.som_cinza)
        self._som_azul = QCheckBox("Som baú azul"); self._som_azul.setChecked(config.som_azul)
        lay.addWidget(self._som_cinza); lay.addWidget(self._som_azul)
        vol = QHBoxLayout(); vol.addWidget(QLabel("Volume"))
        self._volume = QSlider(Qt.Horizontal); self._volume.setRange(0, 100); self._volume.setValue(config.volume)
        vol.addWidget(self._volume); lay.addLayout(vol)

        inter = QHBoxLayout(); inter.addWidget(QLabel("Intervalo de leitura (s)"))
        self._intervalo = QSpinBox(); self._intervalo.setRange(1, 60); self._intervalo.setValue(config.intervalo_seg)
        inter.addWidget(self._intervalo); lay.addLayout(inter)

        logrow = QHBoxLayout()
        self._log = QLineEdit(config.log_path)
        btn_log = QPushButton("..."); btn_log.clicked.connect(self._escolher_log)
        logrow.addWidget(self._log); logrow.addWidget(btn_log)
        lay.addWidget(QLabel("Caminho do Player.log:")); lay.addLayout(logrow)

        botoes = QHBoxLayout()
        ok = QPushButton("Salvar"); ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        botoes.addStretch(); botoes.addWidget(ok); botoes.addWidget(cancel)
        lay.addLayout(botoes)

    def _recarregar_lista(self) -> None:
        self._lista.clear()
        for ik in self._monitorados_em_edicao:
            try:
                nome = bau_para_item_key(ik).nome
            except ValueError:
                nome = ik
            item = QListWidgetItem(f"{nome}  ({ik})")
            item.setData(Qt.UserRole, ik)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self._lista.addItem(item)

    def _adicionar_conhecido(self) -> None:
        ik = self._combo.currentData()
        if ik and ik not in self._monitorados_em_edicao:
            self._monitorados_em_edicao.append(ik)
            self._recarregar_lista()

    def _adicionar(self) -> None:
        ik = self._novo.text().strip()
        try:
            parse_item_key(ik)
        except ValueError:
            self._novo.setStyleSheet(f"border: 2px solid {C.PERIGO};")
            return
        if ik not in self._monitorados_em_edicao:
            self._monitorados_em_edicao.append(ik)
            self._recarregar_lista()
        self._novo.clear(); self._novo.setStyleSheet("")

    def _escolher_log(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecione o Player.log", self._log.text(), "Log (*.log);;Todos (*.*)")
        if caminho:
            self._log.setText(caminho)

    def aplicar(self) -> None:
        """Grava os valores do diálogo de volta no config (chamar após exec() == Accepted)."""
        monitorados = []
        for i in range(self._lista.count()):
            item = self._lista.item(i)
            if item.checkState() == Qt.Checked:
                monitorados.append(item.data(Qt.UserRole))
        self._config.monitorados = monitorados
        self._config.som_cinza = self._som_cinza.isChecked()
        self._config.som_azul = self._som_azul.isChecked()
        self._config.volume = self._volume.value()
        self._config.intervalo_seg = self._intervalo.value()
        self._config.log_path = self._log.text().strip()
        self._config.salvar()
