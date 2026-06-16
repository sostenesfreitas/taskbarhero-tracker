"""Acrescenta linhas de drop a um log de teste a cada poucos segundos.
Uso: python tools/simular_log.py <caminho_log>"""
import sys
import time

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
