# TaskBar Hero Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a floating always-on-top desktop widget that watches TaskBar Hero's `Player.log`, and for each monitored chest shows when it becomes available and which stage to farm it on, with sound + visual alerts.

**Architecture:** Pure-Python core (config, catalog, log watcher, tracker) decoupled from the PySide6 UI via Qt signals, so all logic is unit-testable without a display. The log watcher tails the log incrementally; the tracker holds cooldown state on a 1s timer and emits "ready" events that drive alerts and card visuals.

**Tech Stack:** Python 3, PySide6 (QtWidgets, QtCore, QtMultimedia), pytest. Packaged with PyInstaller. Visual style per the user's `DESIGN.md` ("Forja de Ferro").

---

## File Structure

```
taskbarhero-tracker/
├─ main.py                 # entrypoint: wires modules, starts Qt app
├─ requirements.txt
├─ theme.py                # color tokens + QSS string (DESIGN.md §10)
├─ config.py               # JSON load/save, log path auto-detect
├─ catalogo.py             # Bau dataclass, ItemKey parsing, default catalog, stage map
├─ log_watcher.py          # QObject: tail Player.log, emit bau_detectado
├─ rastreador.py           # QObject: cooldown state model, emit bau_ficou_pronto
├─ alertas.py              # sound playback + volume/toggles
├─ ui/
│  ├─ __init__.py
│  ├─ janela.py            # frameless always-on-top main window
│  ├─ card_bau.py          # one chest card widget
│  └─ painel_config.py     # settings dialog
├─ assets/
│  ├─ icones/  (Item_910011.png cinza, Item_920011.png azul, Item_930011.png vermelho)
│  ├─ fonts/   (downloaded in Task 0)
│  └─ sons/    (placeholder wavs in Task 0)
└─ tests/
   ├─ test_catalogo.py
   ├─ test_config.py
   ├─ test_log_watcher.py
   └─ test_rastreador.py
```

**Responsibilities:**
- `catalogo.py` — pure data: what a chest *is* (type, level, rarity, stage, cooldown). No Qt.
- `config.py` — pure data + filesystem: user choices + log path. No Qt.
- `log_watcher.py` — turns log file bytes into `bau_detectado` signals.
- `rastreador.py` — turns detections + time into cooldown state + `bau_ficou_pronto`.
- `alertas.py` — turns "ready" into sound.
- `ui/*` — turns state into pixels; holds no business logic.

`catalogo.py`, `config.py`, `rastreador.py` use injected `relogio` (a `now()` callable, default `datetime.now`) so tests control time without sleeping.

---

## Task 0: Project scaffold + assets + dependencies

**Files:**
- Create: `taskbarhero-tracker/requirements.txt`
- Create: `taskbarhero-tracker/ui/__init__.py` (empty)
- Create: `taskbarhero-tracker/tests/__init__.py` (empty)
- Assets: `assets/fonts/`, `assets/sons/`

- [ ] **Step 1: Write requirements.txt**

```
PySide6>=6.6
```

(pytest is a dev tool; install separately. PySide6 includes QtMultimedia.)

- [ ] **Step 2: Create empty package markers**

Create `ui/__init__.py` and `tests/__init__.py` as empty files.

- [ ] **Step 3: Install dependencies**

Run: `python -m pip install PySide6 pytest`
Expected: installs without error. Verify: `python -c "import PySide6; print(PySide6.__version__)"`

- [ ] **Step 4: Download free pixel fonts into assets/fonts/**

Download these `.ttf` files (Open Font License / free) into `assets/fonts/`:
- `PressStart2P-Regular.ttf` — https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf
- `PixelifySans-Regular.ttf` — https://github.com/google/fonts/raw/main/ofl/pixelifysans/PixelifySans%5Bwght%5D.ttf (variable; rename to PixelifySans-Regular.ttf)
- `DepartureMono-Regular.ttf` — https://github.com/rektdeckard/departure-mono/raw/main/fonts/ttf/DepartureMono-Regular.ttf

PowerShell example:
```powershell
$ua="Mozilla/5.0"; $f="assets/fonts"
Invoke-WebRequest "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf" -UserAgent $ua -UseBasicParsing -OutFile "$f/PressStart2P-Regular.ttf"
Invoke-WebRequest "https://github.com/rektdeckard/departure-mono/raw/main/fonts/ttf/DepartureMono-Regular.ttf" -UserAgent $ua -UseBasicParsing -OutFile "$f/DepartureMono-Regular.ttf"
Invoke-WebRequest "https://github.com/google/fonts/raw/main/ofl/pixelifysans/PixelifySans%5Bwght%5D.ttf" -UserAgent $ua -UseBasicParsing -OutFile "$f/PixelifySans-Regular.ttf"
```
If any download fails, the app must still run (fonts have a system-mono fallback, handled in Task 8). Note which succeeded.

- [ ] **Step 5: Create placeholder sound files**

Generate two short WAV files with Python's stdlib `wave` (no external deps):
```python
import wave, struct, math, os
os.makedirs("assets/sons", exist_ok=True)
def beep(path, freq, ms=400, rate=44100):
    n = int(rate * ms / 1000)
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        for i in range(n):
            env = min(1.0, i/2000) * min(1.0, (n-i)/4000)  # fade in/out
            w.writeframes(struct.pack("<h", int(env*12000*math.sin(2*math.pi*freq*i/rate))))
beep("assets/sons/cinza.wav", 660)
beep("assets/sons/azul.wav", 880)
```
Run it once. Expected: two `.wav` files exist in `assets/sons/`.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: scaffold project, deps, fonts, placeholder sounds"
```

---

## Task 1: Catalog — Bau dataclass, ItemKey parsing, defaults

**Files:**
- Create: `taskbarhero-tracker/catalogo.py`
- Test: `taskbarhero-tracker/tests/test_catalogo.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_catalogo.py
import pytest
from catalogo import parse_item_key, bau_para_item_key, CATALOGO_PADRAO, STAGE_POR_NIVEL

def test_parse_cinza_lv65():
    info = parse_item_key("910651")
    assert info["tipo"] == "cinza"
    assert info["nivel"] == 65
    assert info["cooldown_seg"] == 300

def test_parse_azul_lv80():
    info = parse_item_key("920801")
    assert info["tipo"] == "azul"
    assert info["nivel"] == 80
    assert info["cooldown_seg"] == 420

def test_parse_vermelho_lv50():
    info = parse_item_key("930501")
    assert info["tipo"] == "vermelho"
    assert info["nivel"] == 50

def test_parse_invalido():
    with pytest.raises(ValueError):
        parse_item_key("123")

def test_stage_por_nivel():
    assert STAGE_POR_NIVEL[50] == ("Pesadelo", "3-5")
    assert STAGE_POR_NIVEL[65] == ("Inferno", "2-5")
    assert STAGE_POR_NIVEL[80] == ("Tormento", "1-3")

def test_bau_para_item_key_resolve_tudo():
    bau = bau_para_item_key("920651")
    assert bau.tipo == "azul"
    assert bau.nivel == 65
    assert bau.raridade == "raro"
    assert bau.stage_dificuldade == "Inferno"
    assert bau.stage_range == "2-5"
    assert bau.cooldown_seg == 420
    assert bau.nome == "Stage Boss Box Lv65"

def test_catalogo_padrao_tem_6_monitorados():
    # default monitored = cinza+azul Lv50/65/80
    assert set(CATALOGO_PADRAO) == {"910501","910651","910801","920501","920651","920801"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_catalogo.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'catalogo'`

- [ ] **Step 3: Write the implementation**

```python
# catalogo.py
from dataclasses import dataclass

TIPO_POR_PREFIXO = {"91": "cinza", "92": "azul", "93": "vermelho"}
RARIDADE_POR_TIPO = {"cinza": "comum", "azul": "raro", "vermelho": "epico"}
COOLDOWN_POR_TIPO = {"cinza": 300, "azul": 420, "vermelho": 420}
NOME_POR_TIPO = {"cinza": "Normal Monster Box", "azul": "Stage Boss Box", "vermelho": "Act Boss Box"}
ICONE_POR_TIPO = {"cinza": "Item_910011.png", "azul": "Item_920011.png", "vermelho": "Item_930011.png"}

# Da Imagem #2: nível -> (dificuldade, range de stage recomendado)
STAGE_POR_NIVEL = {
    50: ("Pesadelo", "3-5"),
    65: ("Inferno", "2-5"),
    80: ("Tormento", "1-3"),
}
# Lv40 não tem stage recomendado na imagem; cai num default neutro.
STAGE_DEFAULT = ("Normal", "1-1")

# Monitorados por padrão na v1: cinza+azul Lv50/65/80
CATALOGO_PADRAO = ["910501", "910651", "910801", "920501", "920651", "920801"]


def parse_item_key(item_key: str) -> dict:
    """Extrai tipo, nivel e cooldown de um ItemKey no formato 9[1|2|3]0<LV><1>."""
    s = str(item_key)
    if len(s) != 6 or not s.isdigit() or s[:2] not in TIPO_POR_PREFIXO:
        raise ValueError(f"ItemKey inválido: {item_key!r}")
    tipo = TIPO_POR_PREFIXO[s[:2]]
    nivel = int(s[2:5])  # ex.: '065' -> 65, '050' -> 50, '080' -> 80, '040' -> 40
    return {"tipo": tipo, "nivel": nivel, "cooldown_seg": COOLDOWN_POR_TIPO[tipo]}


@dataclass(frozen=True)
class Bau:
    item_key: str
    tipo: str           # 'cinza' | 'azul' | 'vermelho'
    nivel: int
    raridade: str       # 'comum' | 'raro' | 'epico'
    cooldown_seg: int
    stage_dificuldade: str
    stage_range: str
    nome: str
    icone: str          # nome do arquivo em assets/icones/


def bau_para_item_key(item_key: str) -> Bau:
    info = parse_item_key(item_key)
    tipo, nivel = info["tipo"], info["nivel"]
    dificuldade, srange = STAGE_POR_NIVEL.get(nivel, STAGE_DEFAULT)
    return Bau(
        item_key=str(item_key),
        tipo=tipo,
        nivel=nivel,
        raridade=RARIDADE_POR_TIPO[tipo],
        cooldown_seg=info["cooldown_seg"],
        stage_dificuldade=dificuldade,
        stage_range=srange,
        nome=f"{NOME_POR_TIPO[tipo]} Lv{nivel}",
        icone=ICONE_POR_TIPO[tipo],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_catalogo.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add catalogo.py tests/test_catalogo.py
git commit -m "feat: chest catalog with ItemKey parsing and stage map"
```

---

## Task 2: Config — JSON load/save + log path auto-detect

**Files:**
- Create: `taskbarhero-tracker/config.py`
- Test: `taskbarhero-tracker/tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config.py
import json
from config import Config, DEFAULTS

def test_defaults_quando_arquivo_nao_existe(tmp_path):
    c = Config(tmp_path / "naoexiste.json")
    assert c.monitorados == DEFAULTS["monitorados"]
    assert c.volume == DEFAULTS["volume"]
    assert c.som_cinza is True and c.som_azul is True
    assert c.intervalo_seg == 5

def test_round_trip_save_load(tmp_path):
    p = tmp_path / "config.json"
    c = Config(p)
    c.volume = 70
    c.monitorados = ["910651", "920651"]
    c.janela_pos = [100, 200]
    c.salvar()
    c2 = Config(p)
    assert c2.volume == 70
    assert c2.monitorados == ["910651", "920651"]
    assert c2.janela_pos == [100, 200]

def test_json_corrompido_recria_padroes(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{ isto não é json", encoding="utf-8")
    c = Config(p)
    assert c.monitorados == DEFAULTS["monitorados"]
    assert (tmp_path / "config.json.bak").exists()

def test_auto_detect_log_path_formato():
    # não exige que o arquivo exista, só o formato do caminho padrão
    from config import log_path_padrao
    p = log_path_padrao()
    assert p.endswith("Player.log")
    assert "TesseractStudio" in p and "TaskbarHero" in p
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config'`

- [ ] **Step 3: Write the implementation**

```python
# config.py
import json
import os
from pathlib import Path
from catalogo import CATALOGO_PADRAO


def log_path_padrao() -> str:
    base = os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\TesseractStudio\TaskbarHero")
    return str(Path(base) / "Player.log")


DEFAULTS = {
    "log_path": log_path_padrao(),
    "intervalo_seg": 5,
    "monitorados": list(CATALOGO_PADRAO),
    "som_cinza": True,
    "som_azul": True,
    "volume": 40,
    "janela_pos": [80, 80],
    "stages_custom": {},   # {item_key: {"dificuldade": str, "range": str}}
}


class Config:
    def __init__(self, caminho: Path | str | None = None):
        self.caminho = Path(caminho) if caminho else _config_path_padrao()
        dados = self._carregar()
        for chave, padrao in DEFAULTS.items():
            setattr(self, chave, dados.get(chave, padrao))

    def _carregar(self) -> dict:
        if not self.caminho.exists():
            return {}
        try:
            return json.loads(self.caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # backup e recria
            try:
                self.caminho.replace(self.caminho.with_suffix(self.caminho.suffix + ".bak"))
            except OSError:
                pass
            return {}

    def salvar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = {chave: getattr(self, chave) for chave in DEFAULTS}
        self.caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")


def _config_path_padrao() -> Path:
    base = os.path.expandvars(r"%APPDATA%\TaskBarHeroTracker")
    return Path(base) / "config.json"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_config.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: JSON config with defaults, backup recovery, log auto-detect"
```

---

## Task 3: Log watcher — tail Player.log, emit detections

**Files:**
- Create: `taskbarhero-tracker/log_watcher.py`
- Test: `taskbarhero-tracker/tests/test_log_watcher.py`

The watcher core logic (reading new bytes, parsing) is split from the QTimer so it's
testable without Qt's event loop. We test `LogReader` (pure) directly.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_log_watcher.py
from log_watcher import LogReader

LINHA = "GetBoxCount Success Count : 1 // ItemKey : {}\n"

def test_seek_to_end_ignora_historico(tmp_path):
    p = tmp_path / "Player.log"
    p.write_text(LINHA.format("910651") + LINHA.format("920651"), encoding="utf-8")
    r = LogReader(p)
    r.seek_to_end()
    assert r.ler_novos() == []   # nada novo após seek-to-end

def test_detecta_linhas_novas(tmp_path):
    p = tmp_path / "Player.log"
    p.write_text("ruído inicial\n", encoding="utf-8")
    r = LogReader(p)
    r.seek_to_end()
    with p.open("a", encoding="utf-8") as f:
        f.write(LINHA.format("910651"))
        f.write("linha irrelevante\n")
        f.write(LINHA.format("920801"))
    assert r.ler_novos() == ["910651", "920801"]

def test_arquivo_inexistente_retorna_vazio(tmp_path):
    r = LogReader(tmp_path / "naoexiste.log")
    assert r.ler_novos() == []

def test_truncamento_reabre_do_inicio(tmp_path):
    p = tmp_path / "Player.log"
    p.write_text(LINHA.format("910651") * 3, encoding="utf-8")
    r = LogReader(p)
    r.seek_to_end()
    # log foi rotacionado: agora é menor que o offset guardado
    p.write_text(LINHA.format("920651"), encoding="utf-8")
    assert r.ler_novos() == ["920651"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_log_watcher.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'log_watcher'`

- [ ] **Step 3: Write the implementation**

```python
# log_watcher.py
import re
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

PADRAO = re.compile(r"GetBoxCount Success Count : (\d+) // ItemKey : (\d+)")


class LogReader:
    """Lógica pura de tail (sem Qt): guarda offset, lê só bytes novos."""

    def __init__(self, caminho: Path | str):
        self.caminho = Path(caminho)
        self._offset = 0

    def seek_to_end(self) -> None:
        try:
            self._offset = self.caminho.stat().st_size
        except OSError:
            self._offset = 0

    def ler_novos(self) -> list[str]:
        """Retorna a lista de ItemKeys das linhas acrescentadas desde a última leitura."""
        try:
            tamanho = self.caminho.stat().st_size
        except OSError:
            return []
        if tamanho < self._offset:   # truncado/rotacionado
            self._offset = 0
        if tamanho == self._offset:
            return []
        with self.caminho.open("r", encoding="utf-8", errors="ignore") as f:
            f.seek(self._offset)
            trecho = f.read()
            self._offset = f.tell()
        return [m.group(2) for m in PADRAO.finditer(trecho)]


class LogWatcher(QObject):
    """Embrulho Qt: chama LogReader.ler_novos() num QTimer e emite sinal por ItemKey."""

    bau_detectado = Signal(str)   # item_key

    def __init__(self, caminho: Path | str, intervalo_seg: int = 5, parent=None):
        super().__init__(parent)
        self._reader = LogReader(caminho)
        self._timer = QTimer(self)
        self._timer.setInterval(intervalo_seg * 1000)
        self._timer.timeout.connect(self._tick)

    def iniciar(self) -> None:
        self._reader.seek_to_end()   # não alerta histórico
        self._timer.start()

    def parar(self) -> None:
        self._timer.stop()

    def definir_caminho(self, caminho: Path | str) -> None:
        self._reader = LogReader(caminho)
        if self._timer.isActive():
            self._reader.seek_to_end()

    def definir_intervalo(self, intervalo_seg: int) -> None:
        self._timer.setInterval(intervalo_seg * 1000)

    def _tick(self) -> None:
        for item_key in self._reader.ler_novos():
            self.bau_detectado.emit(item_key)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_log_watcher.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add log_watcher.py tests/test_log_watcher.py
git commit -m "feat: incremental log tail with seek-to-end and truncation handling"
```

---

## Task 4: Rastreador — cooldown state model + ready events

**Files:**
- Create: `taskbarhero-tracker/rastreador.py`
- Test: `taskbarhero-tracker/tests/test_rastreador.py`

State logic is pure (`EstadoBau` + `Rastreador`); a thin QObject wrapper exposes signals.
Time is injected via `relogio` so tests don't sleep.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_rastreador.py
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
    r.detectado("999999")  # não monitorado
    assert r.estado("999999") is None

def test_redeteccao_reinicia_cooldown():
    estado, relogio = make_relogio(datetime(2026, 6, 16, 12, 0, 0))
    r = Rastreador(["920651"], relogio=relogio)  # azul, 420s
    r.detectado("920651")
    estado["agora"] += timedelta(seconds=500)
    r.tick()
    assert r.estado("920651").estado == "pronto"
    r.detectado("920651")   # dropou de novo
    assert r.estado("920651").estado == "cooldown"
    assert r.estado("920651").restante_seg == 420

def test_estado_inicial_nunca():
    estado, relogio = make_relogio(datetime(2026, 6, 16, 12, 0, 0))
    r = Rastreador(["910651"], relogio=relogio)
    assert r.estado("910651").estado == "nunca"
    assert r.estado("910651").restante_seg == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_rastreador.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'rastreador'`

- [ ] **Step 3: Write the implementation**

```python
# rastreador.py
from dataclasses import dataclass, field
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
    """Mantém o estado de cooldown de cada baú monitorado. Tempo injetável via `relogio`."""

    def __init__(self, monitorados: list[str], relogio=datetime.now):
        self._relogio = relogio
        self._callbacks_pronto = []
        self._estados: dict[str, EstadoBau] = {}
        for ik in monitorados:
            self._estados[str(ik)] = EstadoBau(bau=bau_para_item_key(ik))

    def on_pronto(self, cb) -> None:
        self._callbacks_pronto.append(cb)

    def estado(self, item_key: str) -> EstadoBau | None:
        return self._estados.get(str(item_key))

    def estados(self) -> list[EstadoBau]:
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
```

Note: `restante_seg` rounds up so a fresh detection reads exactly `cooldown_seg` (300/420),
matching the tests.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_rastreador.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add rastreador.py tests/test_rastreador.py
git commit -m "feat: cooldown tracker with injectable clock and ready events"
```

---

## Task 5: Theme — color tokens + QSS

**Files:**
- Create: `taskbarhero-tracker/theme.py`

No unit test (pure styling strings); validated via the UI smoke test in Task 8.

- [ ] **Step 1: Write theme.py**

```python
# theme.py  — tokens da Forja de Ferro (DESIGN.md §2/§10)
class C:
    OBSIDIANA = "#140C0C"; COURO = "#3D1413"; COURO_CLARO = "#511A17"; BREU = "#0B0707"
    OURO = "#CAA53A"; OURO_BRILHO = "#F0D985"; OURO_SOMBRA = "#6B4F17"; LATAO = "#8B6914"
    BANNER_TOPO = "#A82A23"; BANNER_BASE = "#6E1714"
    TEXTO_OURO = "#F4CA4D"; TEXTO_OSSO = "#E7DCC4"; TEXTO_MUDO = "#9A8A72"
    SLOT = "#27313E"; SLOT_VAZIO = "#181E26"
    RAR_COMUM = "#8A8A8A"; RAR_RARO = "#3F7FD6"; RAR_EPICO = "#9A4FD6"
    PERIGO = "#C0392B"; MARCADOR = "#3FAE4A"

# cor da borda do card por raridade
COR_RARIDADE = {"comum": C.RAR_COMUM, "raro": C.RAR_RARO, "epico": C.RAR_EPICO}

QSS = """
QWidget {{ background: {COURO}; color: {TEXTO_OSSO};
           font-family: 'Pixelify Sans'; font-size: 14px; }}
QFrame#Moldura {{
    background: {COURO};
    border-top: 3px solid {OURO_BRILHO}; border-left: 3px solid {OURO};
    border-right: 3px solid {OURO_SOMBRA}; border-bottom: 3px solid {OURO_SOMBRA};
}}
QFrame#TituloBarra {{
    background: qlineargradient(x1:0,y1:0, x2:0,y2:1, stop:0 {BANNER_TOPO}, stop:1 {BANNER_BASE});
    border: 2px solid {OURO};
}}
QLabel#TituloTexto {{ font-family: 'Press Start 2P'; color: {TEXTO_OURO}; font-size: 12px; }}
QLabel#Stage {{ color: {TEXTO_OURO}; font-family: 'Pixelify Sans'; font-size: 14px; }}
QLabel#Tempo {{ font-family: 'Departure Mono'; font-size: 16px; color: {TEXTO_OSSO}; }}
QLabel#Status {{ color: {TEXTO_MUDO}; font-size: 12px; }}
QFrame#Card {{ background: {OBSIDIANA}; border: 2px solid {RAR_COMUM}; }}
QFrame#Card[raridade="raro"] {{ border-color: {RAR_RARO}; }}
QFrame#Card[raridade="epico"] {{ border-color: {RAR_EPICO}; }}
QFrame#Card[pronto="true"] {{ border-color: {MARCADOR}; }}
QProgressBar {{ background: {SLOT_VAZIO}; border: 2px solid {OURO_SOMBRA};
                text-align: center; color: {TEXTO_OSSO}; }}
QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                       stop:0 {LATAO}, stop:1 {OURO_BRILHO}); }}
QProgressBar[pronto="true"]::chunk {{ background: {MARCADOR}; }}
QPushButton {{ background: {COURO}; border: 2px solid {OURO}; color: {TEXTO_OSSO}; padding: 4px 10px; }}
QPushButton:hover {{ border-color: {OURO_BRILHO}; background: {COURO_CLARO}; }}
QPushButton:disabled {{ color: {TEXTO_MUDO}; border-color: {OURO_SOMBRA}; }}
QToolTip {{ background: {OBSIDIANA}; color: {TEXTO_OSSO}; border: 1px solid {OURO}; }}
""".format(**{k: v for k, v in vars(C).items() if not k.startswith("_")})
```

- [ ] **Step 2: Verify it imports**

Run: `cd taskbarhero-tracker && python -c "import theme; print('ok', len(theme.QSS))"`
Expected: prints `ok` and a number > 0 (no KeyError from `.format`).

- [ ] **Step 3: Commit**

```bash
git add theme.py
git commit -m "feat: Forja de Ferro theme tokens and QSS"
```

---

## Task 6: Alertas — sound playback

**Files:**
- Create: `taskbarhero-tracker/alertas.py`

No unit test (audio side-effect + Qt multimedia); validated in the integration run (Task 9).
Must degrade silently if a sound file is missing.

- [ ] **Step 1: Write alertas.py**

```python
# alertas.py
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from utils import asset_path


class Alertas:
    """Toca som por tipo de baú, respeitando toggles e volume da config."""

    def __init__(self, config):
        self._config = config
        self._efeitos: dict[str, QSoundEffect] = {}
        for tipo, arq in (("cinza", "cinza.wav"), ("azul", "azul.wav")):
            caminho = asset_path(f"sons/{arq}")
            if Path(caminho).exists():
                ef = QSoundEffect()
                ef.setSource(QUrl.fromLocalFile(caminho))
                self._efeitos[tipo] = ef

    def tocar(self, tipo: str) -> None:
        ativo = {"cinza": self._config.som_cinza, "azul": self._config.som_azul}.get(tipo, True)
        if not ativo:
            return
        ef = self._efeitos.get(tipo)
        if ef is None:
            return  # arquivo ausente -> silêncio, sem crash
        ef.setVolume(max(0.0, min(1.0, self._config.volume / 100.0)))
        ef.play()
```

- [ ] **Step 2: Create utils.py with asset_path (used here and in UI)**

```python
# utils.py
import sys
from pathlib import Path

def asset_path(rel: str) -> str:
    """Caminho de um asset, funcionando em dev e empacotado (PyInstaller _MEIPASS)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return str(base / "assets" / rel)
```

- [ ] **Step 3: Verify import (without playing)**

Run: `cd taskbarhero-tracker && python -c "import utils; print(utils.asset_path('sons/cinza.wav'))"`
Expected: prints a path ending in `assets/sons/cinza.wav`.

- [ ] **Step 4: Commit**

```bash
git add alertas.py utils.py
git commit -m "feat: per-type sound alerts with volume and graceful fallback"
```

---

## Task 7: Card widget

**Files:**
- Create: `taskbarhero-tracker/ui/card_bau.py`

UI widget; validated by the smoke test in Task 8. Receives an `EstadoBau` and renders it.

- [ ] **Step 1: Write ui/card_bau.py**

```python
# ui/card_bau.py
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                               QProgressBar, QGraphicsOpacityEffect)

from utils import asset_path
from theme import COR_RARIDADE


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
        """Animação curta ao ficar pronto (DESIGN.md §8)."""
        efeito = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(efeito)
        anim = QPropertyAnimation(efeito, b"opacity", self)
        anim.setDuration(150); anim.setStartValue(0.3); anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._anim = anim
```

- [ ] **Step 2: Verify import**

Run: `cd taskbarhero-tracker && python -c "from ui import card_bau; print('ok')"`
Expected: prints `ok` (may print a Qt platform warning; that's fine).

- [ ] **Step 3: Commit**

```bash
git add ui/card_bau.py
git commit -m "feat: chest card widget with cooldown bar and ready state"
```

---

## Task 8: Main window + UI smoke test

**Files:**
- Create: `taskbarhero-tracker/ui/janela.py`
- Test: `taskbarhero-tracker/tests/test_ui_smoke.py`

- [ ] **Step 1: Write the failing smoke test**

```python
# tests/test_ui_smoke.py
import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # roda sem display

@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication
    a = QApplication.instance() or QApplication([])
    yield a

def test_janela_instancia_com_cards(app, tmp_path):
    from config import Config
    from rastreador import Rastreador
    from ui.janela import Janela
    cfg = Config(tmp_path / "config.json")
    cfg.monitorados = ["910651", "920651"]
    rast = Rastreador(cfg.monitorados)
    janela = Janela(cfg, rast, alertas=None)
    assert janela.contar_cards() == 2

def test_carregar_fontes_nao_quebra(app):
    from ui.janela import carregar_fontes
    carregar_fontes()  # não deve lançar mesmo se faltar .ttf
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_ui_smoke.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ui.janela'`

- [ ] **Step 3: Write ui/janela.py**

```python
# ui/janela.py
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea)

from utils import asset_path
from ui.card_bau import CardBau


def carregar_fontes() -> None:
    for arq in ("PressStart2P-Regular.ttf", "PixelifySans-Regular.ttf", "DepartureMono-Regular.ttf"):
        try:
            QFontDatabase.addApplicationFont(asset_path(f"fonts/{arq}"))
        except Exception:
            pass  # fonte ausente -> fallback do sistema


class Janela(QWidget):
    def __init__(self, config, rastreador, alertas=None, parent=None):
        super().__init__(parent)
        self._config = config
        self._rastreador = rastreador
        self._alertas = alertas
        self._cards: dict[str, CardBau] = {}
        self._drag_offset = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
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
        # prontos primeiro, depois menor tempo restante, depois nível
        def chave(e):
            return (0 if e.estado == "pronto" else 1, e.restante_seg, e.bau.nivel)
        for e in sorted(self._rastreador.estados(), key=chave):
            card = CardBau(e)
            self._cards[e.bau.item_key] = card
            self._grade.addWidget(card)

    def atualizar_cards(self) -> None:
        for card in self._cards.values():
            card.atualizar()

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

    # arrastar a janela sem moldura
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, ev):
        if self._drag_offset is not None and ev.buttons() & Qt.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, ev):
        self._drag_offset = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd taskbarhero-tracker && python -m pytest tests/test_ui_smoke.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add ui/janela.py tests/test_ui_smoke.py
git commit -m "feat: frameless always-on-top main window with card grid"
```

---

## Task 9: Settings dialog

**Files:**
- Create: `taskbarhero-tracker/ui/painel_config.py`
- Modify: `taskbarhero-tracker/ui/janela.py` (add ⚙ button that opens the dialog)

- [ ] **Step 1: Write ui/painel_config.py**

```python
# ui/painel_config.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                               QSlider, QSpinBox, QListWidget, QListWidgetItem, QPushButton,
                               QLineEdit, QFileDialog, QWidget)
from PySide6.QtCore import Qt

from catalogo import bau_para_item_key, parse_item_key


class PainelConfig(QDialog):
    """Edita config: baús monitorados, sons, volume, intervalo, caminho do log."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Configurações")
        lay = QVBoxLayout(self)

        # lista de monitorados com checkbox
        lay.addWidget(QLabel("Baús monitorados:"))
        self._lista = QListWidget()
        self._recarregar_lista()
        lay.addWidget(self._lista)

        # adicionar por ItemKey
        addrow = QHBoxLayout()
        self._novo = QLineEdit(); self._novo.setPlaceholderText("ItemKey (ex.: 930801)")
        btn_add = QPushButton("Adicionar"); btn_add.clicked.connect(self._adicionar)
        addrow.addWidget(self._novo); addrow.addWidget(btn_add)
        lay.addLayout(addrow)

        # sons + volume
        self._som_cinza = QCheckBox("Som baú cinza"); self._som_cinza.setChecked(config.som_cinza)
        self._som_azul = QCheckBox("Som baú azul"); self._som_azul.setChecked(config.som_azul)
        lay.addWidget(self._som_cinza); lay.addWidget(self._som_azul)
        vol = QHBoxLayout(); vol.addWidget(QLabel("Volume"))
        self._volume = QSlider(Qt.Horizontal); self._volume.setRange(0, 100); self._volume.setValue(config.volume)
        vol.addWidget(self._volume); lay.addLayout(vol)

        # intervalo
        inter = QHBoxLayout(); inter.addWidget(QLabel("Intervalo de leitura (s)"))
        self._intervalo = QSpinBox(); self._intervalo.setRange(1, 60); self._intervalo.setValue(config.intervalo_seg)
        inter.addWidget(self._intervalo); lay.addLayout(inter)

        # caminho do log
        logrow = QHBoxLayout()
        self._log = QLineEdit(config.log_path)
        btn_log = QPushButton("..."); btn_log.clicked.connect(self._escolher_log)
        logrow.addWidget(self._log); logrow.addWidget(btn_log)
        lay.addWidget(QLabel("Caminho do Player.log:")); lay.addLayout(logrow)

        # salvar/cancelar
        botoes = QHBoxLayout()
        ok = QPushButton("Salvar"); ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        botoes.addStretch(); botoes.addWidget(ok); botoes.addWidget(cancel)
        lay.addLayout(botoes)

    def _recarregar_lista(self) -> None:
        self._lista.clear()
        # mostra os monitorados atuais; permite desmarcar para remover
        for ik in self._config.monitorados:
            try:
                nome = bau_para_item_key(ik).nome
            except ValueError:
                nome = ik
            item = QListWidgetItem(f"{nome}  ({ik})")
            item.setData(Qt.UserRole, ik)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self._lista.addItem(item)

    def _adicionar(self) -> None:
        ik = self._novo.text().strip()
        try:
            parse_item_key(ik)
        except ValueError:
            self._novo.setStyleSheet("border: 2px solid #C0392B;")
            return
        if ik not in self._config.monitorados:
            self._config.monitorados.append(ik)
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
```

- [ ] **Step 2: Wire the ⚙ button into janela.py**

In `ui/janela.py`, in `_construir_titulo`, add a settings button before the close button:
```python
        cfgbtn = QPushButton("⚙"); cfgbtn.setFixedSize(24, 24); cfgbtn.clicked.connect(self._abrir_config)
        h.addWidget(cfgbtn)
```
And add this method + signal to `Janela` (after `_fechar`):
```python
    # sinal para o main reconstruir watcher/rastreador quando a config muda
    from PySide6.QtCore import Signal  # (mover para o topo do arquivo)
    config_alterada = Signal()

    def _abrir_config(self) -> None:
        from ui.painel_config import PainelConfig
        dlg = PainelConfig(self._config, self)
        if dlg.exec():
            dlg.aplicar()
            self.config_alterada.emit()
```
**Important:** `Signal` must be declared as a class attribute at the top of `Janela` (not inside a method). Move `config_alterada = Signal()` up to just under `class Janela(QWidget):` and add `Signal` to the `QtCore` import line at the top. The snippet above shows intent; place it correctly.

- [ ] **Step 3: Verify import + smoke test still passes**

Run: `cd taskbarhero-tracker && python -c "from ui.painel_config import PainelConfig; print('ok')" && python -m pytest tests/test_ui_smoke.py -v`
Expected: prints `ok`; smoke tests PASS.

- [ ] **Step 4: Commit**

```bash
git add ui/painel_config.py ui/janela.py
git commit -m "feat: settings dialog (chests, sounds, volume, interval, log path)"
```

---

## Task 10: main.py — wire everything together

**Files:**
- Create: `taskbarhero-tracker/main.py`

- [ ] **Step 1: Write main.py**

```python
# main.py
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from config import Config
from rastreador import Rastreador
from log_watcher import LogWatcher
from alertas import Alertas
from theme import QSS
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

        # tick de 1s atualiza estado + UI
        self.ui_timer = QTimer()
        self.ui_timer.setInterval(1000)
        self.ui_timer.timeout.connect(self._tick)
        self.ui_timer.start()
        self.watcher.iniciar()

    def _tick(self):
        self.rastreador.tick()
        self.janela.atualizar_cards()

    def _reconfigurar(self):
        # aplica mudanças de config: monitorados, intervalo, caminho do log
        self.rastreador.definir_monitorados(self.config.monitorados)
        self.watcher.definir_intervalo(self.config.intervalo_seg)
        self.watcher.definir_caminho(self.config.log_path)
        self.janela.recriar_cards()

    def run(self):
        self.janela.show()


def main():
    app = QApplication(sys.argv)
    carregar_fontes()
    app.setStyleSheet(QSS)
    a = App()
    a.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add `recriar_cards` to janela.py**

`_reconfigurar` calls `janela.recriar_cards()` — add this method to `Janela` (it clears the
grid and repopulates from the current rastreador estados):
```python
    def recriar_cards(self) -> None:
        for card in self._cards.values():
            card.setParent(None)
        self._cards.clear()
        self._popular_cards()
```

- [ ] **Step 3: Run the app manually (visual verification)**

Run: `cd taskbarhero-tracker && python main.py`
Expected: a small framed always-on-top window appears with one card per monitored chest,
showing the chest icon, name, stage, and `--:--` (state "nunca"). Drag it by clicking the
body. Open ⚙, toggle a chest off, Save → card disappears. Close with X → window closes and
`config.json` is written under `%APPDATA%\TaskBarHeroTracker\`.

If the game is running and a chest drops, within `intervalo_seg` the card enters cooldown;
when it expires it turns green, pulses, plays the sound, and shows "VÁ PARA: ...".

- [ ] **Step 4: Run full test suite**

Run: `cd taskbarhero-tracker && python -m pytest -v`
Expected: all tests PASS (catalogo 7, config 4, log_watcher 4, rastreador 5, ui_smoke 2).

- [ ] **Step 5: Commit**

```bash
git add main.py ui/janela.py
git commit -m "feat: wire app together (watcher -> tracker -> ui + alerts)"
```

---

## Task 11: End-to-end manual verification with a fake log

**Files:**
- Create: `taskbarhero-tracker/tools/simular_log.py` (dev helper, not shipped)

Verifies the whole pipeline without playing the game: a script appends real `GetBoxCount`
lines to a temp log; point the app at it via the settings dialog.

- [ ] **Step 1: Write the simulator**

```python
# tools/simular_log.py
"""Acrescenta linhas de drop a um log de teste a cada poucos segundos.
Uso: python tools/simular_log.py <caminho_log>"""
import sys, time

LINHA = "GetBoxCount Success Count : 1 // ItemKey : {}\n"
SEQ = ["910651", "920651", "910801", "920801", "910501", "920501"]

def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else "fake_player.log"
    open(caminho, "a").close()
    i = 0
    print(f"Escrevendo em {caminho} (Ctrl+C para parar)")
    while True:
        ik = SEQ[i % len(SEQ)]
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(LINHA.format(ik))
        print("drop:", ik)
        i += 1
        time.sleep(8)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Manual E2E run**

1. Terminal A: `cd taskbarhero-tracker && python tools/simular_log.py fake_player.log`
2. Terminal B: `cd taskbarhero-tracker && python main.py`
3. In the app, open ⚙ → set "Caminho do Player.log" to the absolute path of `fake_player.log`
   → set intervalo to 2s → Save.
4. Observe: cards enter cooldown as drops arrive; after 5 min (cinza) / 7 min (azul) they
   turn green, pulse, and play sound. To verify quickly without waiting, temporarily edit
   `COOLDOWN_POR_TIPO` in `catalogo.py` to small values (e.g. 10 and 14), run, then revert.

Expected: the ready transition fires exactly once per chest, the sound respects the
toggles/volume, and "VÁ PARA: <dificuldade> <range>" matches the level (Lv50→Pesadelo 3-5,
Lv65→Inferno 2-5, Lv80→Tormento 1-3).

- [ ] **Step 3: Commit**

```bash
git add tools/simular_log.py
git commit -m "chore: add log simulator for end-to-end manual verification"
```

---

## Task 12: Packaging with PyInstaller

**Files:**
- Create: `taskbarhero-tracker/build.md` (build instructions)

- [ ] **Step 1: Install PyInstaller**

Run: `python -m pip install pyinstaller`
Expected: installs without error.

- [ ] **Step 2: Build the exe**

Run (Windows, from project root):
```
pyinstaller --onefile --windowed --name TaskBarHeroTracker --add-data "assets;assets" main.py
```
Expected: `dist/TaskBarHeroTracker.exe` is produced. The `--add-data "assets;assets"` bundles
icons/fonts/sounds; `utils.asset_path` resolves them via `sys._MEIPASS` at runtime.

- [ ] **Step 3: Run the built exe**

Run: `dist/TaskBarHeroTracker.exe`
Expected: same behavior as `python main.py` — window appears with chest cards, icons load,
fonts apply (or fall back), config persists to `%APPDATA%\TaskBarHeroTracker\config.json`.

- [ ] **Step 4: Write build.md**

```markdown
# Build

1. `python -m pip install -r requirements.txt pyinstaller`
2. `pyinstaller --onefile --windowed --name TaskBarHeroTracker --add-data "assets;assets" main.py`
3. Resultado: `dist/TaskBarHeroTracker.exe`

Os assets (ícones/fontes/sons) são embutidos via `--add-data`. Em dev, são lidos de `./assets`.
```

- [ ] **Step 5: Commit**

```bash
git add build.md
git commit -m "docs: PyInstaller build instructions"
```

---

## Self-Review Notes (for the implementer)

- **Spec coverage:** detecção (Task 3), catálogo+stage (Task 1), cooldown+pronto (Task 4),
  alertas (Task 6), janela flutuante (Task 8), config/adicionar baús (Task 2, 9),
  empacotamento (Task 12), erros: log ausente/truncado (Task 3 + manual), JSON corrompido
  (Task 2), assets ausentes (Task 6/8). Tudo coberto.
- **Time injection:** `Rastreador` recebe `relogio` — testes controlam tempo sem `sleep`.
- **No-Qt-in-logic:** `LogReader`, `catalogo`, `config`, `Rastreador` testáveis sem display;
  UI roda em `QT_QPA_PLATFORM=offscreen` no smoke test.
- **Type consistency:** `bau_para_item_key`/`parse_item_key`, `EstadoBau.restante_seg`/`estado`,
  `Janela.atualizar_cards`/`recriar_cards`/`contar_cards`, `Alertas.tocar(tipo)` usados de forma
  consistente entre tasks.
```
