# Build

1. `python -m pip install -r requirements.txt pyinstaller`
2. `python -m PyInstaller --onefile --windowed --icon "assets/app.ico" --name TaskBarHeroTracker --add-data "assets;assets" main.py`
3. Resultado: `dist/TaskBarHeroTracker.exe`

O ícone do `.exe` (e da janela) é `assets/app.ico`. Para trocar, gere um novo `.ico`
(quadrado, com tamanhos 16–256) e rebuild. Se o Windows continuar mostrando o ícone antigo
no Explorer, é cache de ícones — renomeie/mova o `.exe` ou limpe o cache de ícones.

Os assets (ícones/fontes/sons) são embutidos via `--add-data` e lidos em runtime por
`utils.asset_path` (usa `sys._MEIPASS` quando empacotado). Em desenvolvimento, são lidos de `./assets`.

Se o som não tocar no exe empacotado, rebuild com `--hidden-import PySide6.QtMultimedia`.
