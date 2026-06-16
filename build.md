# Build

1. `python -m pip install -r requirements.txt pyinstaller`
2. `python -m PyInstaller --onefile --windowed --name TaskBarHeroTracker --add-data "assets;assets" main.py`
3. Resultado: `dist/TaskBarHeroTracker.exe`

Os assets (ícones/fontes/sons) são embutidos via `--add-data` e lidos em runtime por
`utils.asset_path` (usa `sys._MEIPASS` quando empacotado). Em desenvolvimento, são lidos de `./assets`.

Se o som não tocar no exe empacotado, rebuild com `--hidden-import PySide6.QtMultimedia`.
