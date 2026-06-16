"""Catálogo de baús (dados puros): parse de ItemKey, dataclass Bau e mapa de stages."""
from dataclasses import dataclass

TIPO_POR_PREFIXO = {"91": "cinza", "92": "azul", "93": "vermelho"}
RARIDADE_POR_TIPO = {"cinza": "comum", "azul": "raro", "vermelho": "epico"}
COOLDOWN_POR_TIPO = {"cinza": 300, "azul": 420, "vermelho": 420}
NOME_POR_TIPO = {"cinza": "Normal Monster Box", "azul": "Stage Boss Box", "vermelho": "Act Boss Box"}
ICONE_POR_TIPO = {"cinza": "Item_910011.png", "azul": "Item_920011.png", "vermelho": "Item_930011.png"}

# Tabela de stages do jogo: nível -> (dificuldade, range de stage recomendado).
# Cobre dos níveis baixos (jogadores fracos) aos altos.
STAGE_POR_NIVEL = {
    1:  ("Normal", "1-1"),
    2:  ("Normal", "1-4"),
    3:  ("Normal", "1-8"),
    15: ("Normal", "2-3"),
    20: ("Normal", "2-8"),
    30: ("Normal", "3-8"),
    40: ("Pesadelo", "1-9"),
    50: ("Pesadelo", "3-5"),
    65: ("Inferno", "2-5"),
    80: ("Tormento", "1-3"),
}
# Nível desconhecido cai num default neutro.
STAGE_DEFAULT = ("Normal", "1-1")

# Ordem dos níveis conhecidos (do mais fraco ao mais forte).
NIVEIS_CONHECIDOS = [1, 2, 3, 15, 20, 30, 40, 50, 65, 80]

# Monitorados por padrão: cinza+azul Lv50/65/80 (Act Boss 93x fica de fora).
CATALOGO_PADRAO = ["910501", "910651", "910801", "920501", "920651", "920801"]


def montar_item_key(tipo: str, nivel: int) -> str:
    """Monta o ItemKey no formato 9[1|2|3]<LLL><1> (prefixo do tipo + nível 3 dígitos + 1)."""
    prefixo = {v: k for k, v in TIPO_POR_PREFIXO.items()}[tipo]
    return f"{prefixo}{nivel:03d}1"


def baus_conhecidos() -> list[str]:
    """ItemKeys de todos os baús cinza+azul conhecidos, do mais fraco ao mais forte.
    Útil para oferecer um menu de escolha (em vez de digitar o ItemKey)."""
    return [montar_item_key(tipo, n) for n in NIVEIS_CONHECIDOS for tipo in ("cinza", "azul")]


def parse_item_key(item_key: str) -> dict:
    """Extrai tipo, nivel e cooldown de um ItemKey no formato 9[1|2|3]0<LV><1>."""
    s = str(item_key)
    if len(s) != 6 or not s.isdigit() or s[:2] not in TIPO_POR_PREFIXO:
        raise ValueError(f"ItemKey inválido: {item_key!r}")
    tipo = TIPO_POR_PREFIXO[s[:2]]
    nivel = int(s[2:5])
    return {"tipo": tipo, "nivel": nivel, "cooldown_seg": COOLDOWN_POR_TIPO[tipo]}


@dataclass(frozen=True)
class Bau:
    item_key: str
    tipo: str            # 'cinza' | 'azul' | 'vermelho'
    nivel: int
    raridade: str        # 'comum' | 'raro' | 'epico'
    cooldown_seg: int
    stage_dificuldade: str
    stage_range: str
    nome: str
    icone: str           # nome do arquivo em assets/icones/


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
