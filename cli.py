#!/usr/bin/env python3
"""CLI interativo — pergunta clínica via terminal."""

import logging
import sys
from core.team_builder import ask

logger = logging.getLogger(__name__)


def main():
    fonte, mode = "auto", "coordinate"
    for arg in sys.argv[1:]:
        if arg in ("rag", "pubmed", "todas"):
            fonte = arg
        elif arg in ("route", "coordinate", "broadcast"):
            mode = arg

    logger.info(f"Fonte: {fonte} | Modo: {mode}")
    print("Pergunta clínica (Ctrl+C para sair):\n")
    try:
        while True:
            q = input(">> ").strip()
            if not q:
                continue
            print("\n" + "─" * 60)
            print(ask(q, fonte=fonte, mode=mode))
            print("─" * 60 + "\n")
    except KeyboardInterrupt:
        print("\nEncerrando.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    main()
