# theme.py  — tokens da Forja de Ferro
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
QLabel#Status {{ color: {TEXTO_MUDO}; font-size: 11px; }}

/* --- Linha compacta (estilo RECORDS) --- */
QFrame#Linha {{ background: {OBSIDIANA}; border: none; border-bottom: 1px solid {BREU}; }}
QFrame#Linha QLabel {{ background: transparent; }}
QLabel#LinhaNome {{ color: {TEXTO_OSSO}; font-family: 'Pixelify Sans'; font-size: 13px; }}
QLabel#LinhaStage {{ color: {TEXTO_MUDO}; font-family: 'Pixelify Sans'; font-size: 12px; }}
QLabel#LinhaTempo {{ color: {TEXTO_OSSO}; font-family: 'Departure Mono'; font-size: 13px; }}
/* azul/cinza: leve tom no nome pela raridade */
QFrame#Linha[raridade="raro"] QLabel#LinhaNome {{ color: {RAR_RARO}; }}
QFrame#Linha[raridade="epico"] QLabel#LinhaNome {{ color: {RAR_EPICO}; }}
/* pronto: a linha inteira fica verde */
QFrame#Linha[pronto="true"] {{ background: rgba(63,174,74,0.14); border-bottom: 1px solid {MARCADOR}; }}
QFrame#Linha[pronto="true"] QLabel {{ color: {MARCADOR}; }}

QPushButton {{ background: {COURO}; border: 2px solid {OURO}; color: {TEXTO_OSSO}; padding: 4px 10px; }}
QPushButton:hover {{ border-color: {OURO_BRILHO}; background: {COURO_CLARO}; }}
QPushButton:disabled {{ color: {TEXTO_MUDO}; border-color: {OURO_SOMBRA}; }}
QToolTip {{ background: {OBSIDIANA}; color: {TEXTO_OSSO}; border: 1px solid {OURO}; }}
""".format(**{k: v for k, v in vars(C).items() if not k.startswith("_")})
