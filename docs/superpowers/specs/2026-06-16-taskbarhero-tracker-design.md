# Spec — TaskBar Hero · Tracker "Pra Onde Ir"

**Data:** 2026-06-16
**Stack:** Python 3 + PySide6 (Qt)
**Estilo visual:** Forja de Ferro (ver `DESIGN.md` fornecido pelo usuário)

---

## 1. Objetivo

Uma janelinha flutuante no desktop que monitora o `Player.log` do jogo TaskBar Hero e,
para cada baú monitorado, responde a duas perguntas:

1. **Este baú está disponível?** (cooldown acabou)
2. **Pra qual stage eu vou farmá-lo?**

Quando um baú fica disponível, o app dispara **alerta sonoro e visual** e destaca o
**stage recomendado**. Não há KPIs, histórico de sessão nem feed de eventos — escopo
deliberadamente enxuto.

### Não-objetivos (YAGNI)
- KPIs / estatísticas de sessão (baús/hora, total detectado, etc.).
- Feed/tabela de eventos da sessão.
- Pity, taxa de drop, registro manual de drop, OCR.
- Persistência em SQLite (usamos JSON).

---

## 2. Mecânica de detecção (confirmada)

O jogo (Unity, dev "TesseractStudio") grava em:

```
C:\Users\<user>\AppData\LocalLow\TesseractStudio\TaskbarHero\Player.log
```

Cada baú dropado gera uma linha:

```
GetBoxCount Success Count : 1 // ItemKey : 920651
```

- O log **não** tem timestamp nessas linhas. O horário de detecção é o momento em que o
  app lê a linha nova (igual ao site de referência, que lê a cada 5s).
- Estrutura do ItemKey: `9[1|2]0<LV><1>` →
  - prefixo `91` = **Normal Monster Box** (cinza), `92` = **Stage Boss Box** (azul),
    `93` = **Act Boss** (vermelho/caveira — fora da v1, addable depois).
  - `<LV>` = nível (40, 50, 65, 80).
- Cooldown a partir da detecção: **cinza = 5 min**, **azul = 7 min**. "Disponível" =
  transição cooldown → pronto.

### ItemKeys da v1
| ItemKey | Tipo | Raridade | Nível | Cooldown |
|---|---|---|---|---|
| 910501 | cinza | comum | Lv50 | 5 min |
| 910651 | cinza | comum | Lv65 | 5 min |
| 910801 | cinza | comum | Lv80 | 5 min |
| 920501 | azul  | raro  | Lv50 | 7 min |
| 920651 | azul  | raro  | Lv65 | 7 min |
| 920801 | azul  | raro  | Lv80 | 7 min |

(Os Lv40 — 910401/920401 — ficam no catálogo mas não são monitorados por padrão na v1.)

### Stage recomendado por nível (da Imagem #2 fornecida pelo usuário)
| Nível | Dificuldade | Stage |
|---|---|---|
| Lv50 | Pesadelo (Nightmare) | 3-5 |
| Lv65 | Inferno (Hell) | 2-5 |
| Lv80 | Tormento (Torment) | 1-3 |

O stage recomendado é **por nível** (vale para cinza e azul do mesmo nível).

---

## 3. Arquitetura

Módulos isolados, cada um com responsabilidade única, comunicando por sinais Qt.

```
Player.log
   │  (tail incremental, lê a cada N s)
   ▼
log_watcher.py ──signal bau_detectado(item_key, ts)──▶ rastreador.py (model)
                                                          │ QTimer 1s recalcula
                                                          ├─signal estado_mudou ──▶ ui/  (atualiza cards)
                                                          └─signal bau_ficou_pronto ─▶ alertas.py (som + pulso)
config.py  ◀──▶  catalogo.py  ◀──  ui/painel_config
```

### 3.1 `log_watcher.py`
- `QObject` com `QTimer` (intervalo configurável, padrão 5s).
- Guarda o **offset** do último byte lido; a cada tick lê só o trecho novo.
- Trata **rotação/truncamento** do log (se o tamanho atual < offset, reabre do início).
- Regex: `GetBoxCount Success Count : (\d+) // ItemKey : (\d+)`.
- Emite `bau_detectado(item_key: str, count: int)` por linha nova. O timestamp é
  carimbado pelo `rastreador` (ou passado como `datetime.now()`).
- **Importante:** no primeiro carregamento, faz "seek to end" (não dispara alertas para
  o histórico já existente no log) — começa a monitorar a partir do estado atual.
- Dependências: caminho do log (do `config`).

### 3.2 `catalogo.py`
- Define `Bau` (dataclass): `item_key, tipo ('cinza'|'azul'|'vermelho'), raridade,
  nivel, stage_dificuldade, stage_range, cooldown_seg, icone_path`.
- `mapa_raridade` (tipo → cor de raridade do DESIGN.md: cinza→comum, azul→raro,
  vermelho→épico/lendário).
- Catálogo padrão com os ItemKeys da seção 2. Função para derivar `tipo`/`nivel` do
  ItemKey (parse `9[1|2|3]0<LV>1`) ao adicionar um baú novo pela config.
- Dependências: nenhuma (dados puros).

### 3.3 `rastreador.py` (model/estado)
- Mantém, por baú monitorado: `ultimo_detectado: datetime|None`,
  `libera_em: datetime|None`, `estado: 'nunca'|'cooldown'|'pronto'`.
- Slot `on_bau_detectado(item_key)`: marca `ultimo_detectado=now`,
  `libera_em=now+cooldown`, estado `cooldown`.
- `QTimer` 1s: recalcula tempo restante; ao cruzar `libera_em`, muda para `pronto` e
  emite `bau_ficou_pronto(item_key)` **uma única vez** por ciclo.
- Emite `estado_mudou()` a cada tick para a UI atualizar barras/tempos.
- Só rastreia baús presentes na lista de monitorados (do `config`).

### 3.4 `alertas.py`
- `tocar(tipo)`: usa `QSoundEffect` (QtMultimedia) para som por tipo (cinza/azul),
  respeitando toggles e volume (0–100) do `config`.
- Sinaliza à UI para o **pulso visual** (borda verde `MARCADOR` + animação curta).
- Sons em `assets/sons/` (incluídos; usuário pode trocar). Se faltar arquivo, degrada
  silenciosamente (sem crash).

### 3.5 `ui/` (PySide6, estilo Forja de Ferro)
- **`janela.py`** — `QWidget` sem moldura (`Qt.FramelessWindowHint`), sempre-no-topo
  (`Qt.WindowStaysOnTopHint`), `Tool` (não aparece na taskbar), fundo translúcido nos
  cantos. Arrastável (mousePress/Move). Moldura via bordas em camadas (DESIGN.md §5),
  com hook para `moldura.png` 9-slice futuro.
- **Barra de título** (DESIGN.md §6.1): banner vermelho + "TASKBAR HERO" em Press Start
  2P dourado + botões: fixar/soltar (toggle always-on-top), config (⚙), minimizar, fechar.
- **Linha de status** curta: "● Monitorando" / "⏸ Pausado", caminho/última leitura
  (discreto). (Sem KPIs.)
- **Grade de cards** (`card_bau.py`) — um card por baú monitorado:
  - ícone pixel oficial (escala inteira, `Qt.FastTransformation`);
  - nome/curto + nível; chip de tipo (cor de raridade);
  - **stage**: "VÁ PARA: Inferno 2-5" (sempre visível);
  - **estado cooldown**: `QProgressBar` (DESIGN.md §6.6, gradiente dourado) + tempo
    `Departure Mono`;
  - **estado pronto**: borda verde `MARCADOR`, pulso 1x, badge "PRONTO", stage destacado.
  - Ordena por: prontos primeiro, depois menor tempo restante.
- **`painel_config.py`** (dialog/aba) — adicionar/remover baús monitorados (escolher do
  catálogo ou inserir ItemKey + stage manual), toggles de som por tipo + volume,
  intervalo de leitura, caminho do `Player.log` (com auto-detect padrão).

### 3.6 `config.py`
- Carrega/salva JSON em `%APPDATA%\TaskBarHeroTracker\config.json` (ou ao lado do exe).
- Campos: `log_path`, `intervalo_seg`, `monitorados: [item_key...]`,
  `som_cinza: bool`, `som_azul: bool`, `volume: int`, `janela_pos: [x,y]`,
  `stages_custom: {item_key: {dificuldade, range}}` (override opcional).
- Auto-detect do `log_path` via `%USERPROFILE%\AppData\LocalLow\TesseractStudio\TaskbarHero\Player.log`.
- Valores padrão se o arquivo não existir.

---

## 4. Fluxo de dados (resumo)

1. App inicia → `config` carrega → `catalogo` resolve baús monitorados → `log_watcher`
   abre o log e faz seek-to-end.
2. A cada N s: lê trecho novo → para cada `ItemKey` monitorado encontrado, emite
   `bau_detectado`.
3. `rastreador` marca detecção e agenda `libera_em`. `QTimer` 1s atualiza UI.
4. Ao zerar cooldown: `bau_ficou_pronto` → `alertas` (som + pulso) e card vira "PRONTO"
   com stage destacado.
5. Usuário vê "pra onde ir", farma, e o ciclo recomeça quando o baú dropar de novo.

---

## 5. Tratamento de erros

- **Log não encontrado:** UI mostra estado "Log não encontrado" + botão para escolher o
  arquivo; não crasha; segue tentando no intervalo.
- **Log rotacionado/truncado:** detectado por tamanho < offset → reabre do início.
- **Linha malformada:** ignorada pelo regex (sem efeito).
- **Asset de som/fonte ausente:** degrada (fonte fallback mono; som silencioso).
- **Config corrompido:** faz backup e recria com padrões.

---

## 6. Testes

- `log_watcher`: dado um arquivo temporário, ao **acrescentar** linhas `GetBoxCount ...`,
  emite `bau_detectado` com os ItemKeys certos; ignora linhas antigas após seek-to-end;
  lida com truncamento.
- `catalogo`: parse de ItemKey → tipo/nível corretos; stage resolvido por nível.
- `rastreador`: após `bau_detectado`, estado=cooldown; avançando o relógio além do
  cooldown (injeção de tempo), emite `bau_ficou_pronto` exatamente uma vez e estado=pronto.
- `config`: round-trip de save/load; auto-detect de caminho; recuperação de JSON inválido.
- UI: smoke test (instancia janela e card sem exceção). Lógica fica fora da UI para ser
  testável sem display.

**Injeção de tempo:** `rastreador` recebe um `relogio=datetime.now` (callable) para os
testes controlarem o tempo sem `sleep`.

---

## 7. Assets

- **Ícones de baú (oficiais do wiki, já baixados em `_thwiki/boxes/`):**
  `Item_910011.png` (cinza), `Item_920011.png` (azul), `Item_930011.png` (vermelho).
  Movidos para `assets/icones/` no projeto.
- **Fontes pixel (grátis):** Press Start 2P, Pixelify Sans (Regular+Bold), Departure Mono
  → baixadas no setup para `assets/fonts/`. Fallback: mono padrão do sistema.
- **Sons:** dois `.wav` curtos em `assets/sons/` (cinza/azul). Placeholder incluído.
- **Moldura:** sem PNG por ora (bordas em camadas do DESIGN.md). Hook para `moldura.png`.

---

## 8. Empacotamento

- PyInstaller → `.exe` único (`--onefile`), assets embutidos via `--add-data`
  (`assets;assets`). Resolução de caminho via `sys._MEIPASS` quando empacotado.
- `requirements.txt`: PySide6.

---

## 9. Estrutura de arquivos

```
taskbarhero-tracker/
├─ main.py
├─ requirements.txt
├─ theme.py                 # tokens de cor + QSS gerado (DESIGN.md §10)
├─ config.py
├─ catalogo.py
├─ log_watcher.py
├─ rastreador.py
├─ alertas.py
├─ ui/
│  ├─ janela.py
│  ├─ card_bau.py
│  └─ painel_config.py
├─ assets/
│  ├─ icones/  (Item_910011.png, Item_920011.png, Item_930011.png)
│  ├─ fonts/
│  └─ sons/
└─ tests/
   ├─ test_log_watcher.py
   ├─ test_catalogo.py
   ├─ test_rastreador.py
   └─ test_config.py
```
