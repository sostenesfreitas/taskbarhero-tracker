from dataclasses import dataclass

TIPO_POR_PREFIXO = {"91": "cinza", "92": "azul", "93": "vermelho"}
RARIDADE_POR_TIPO = {"cinza": "comum", "azul": "raro", "vermelho": "epico"}
COOLDOWN_POR_TIPO = {"cinza": 300, "azul": 420, "vermelho": 420}
NOME_POR_TIPO = {"cinza": "Normal Monster Box", "azul": "Stage Boss Box", "vermelho": "Act Boss Box"}
ICONE_POR_TIPO = {"cinza": "Item_910011.png", "azul": "Item_920011.png", "vermelho": "Item_930011.png"}

STAGE_POR_NIVEL = {
    50: ("Pesadelo", "3-5"),
    65: ("Inferno", "2-5"),
    80: ("Tormento", "1-3"),
}
STAGE_DEFAULT = ("Normal", "1-1")

CATALOGO_PADRAO = ["910501", "910651", "910801", "920501", "920651", "920801"]


def parse_item_key(item_key: str) -> dict:
    """Extrai tipo, nivel e cooldown de um ItemKey no formato 9[1|2|3]0<LV><1>."""
    s = str(item_key)
    if len(s) != 6 or not s.isdigit() or s[:2] not in TIPO_POR_PREFIXO:
        raise ValueError(f"ItemKey invalido: {item_key!r}")
    tipo = TIPO_POR_PREFIXO[s[:2]]
    nivel = int(s[2:5])
    return {"tipo": tipo, "nivel": nivel, "cooldown_seg": COOLDOWN_POR_TIPO[tipo]}


@dataclass(frozen=True)
class Bau:
    item_key: str
    tipo: str
    nivel: int
    raridade: str
    cooldown_seg: int
    stage_dificuldade: str
    stage_range: str
    nome: str
    icone: str


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
