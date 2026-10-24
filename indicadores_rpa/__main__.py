"""CLI: python -m indicadores_rpa --logs exemplos/logs --saida output/indicadores_rpa.xlsx"""

import argparse
import logging
from pathlib import Path

from .excel import gerar_planilha
from .kpis import MINUTOS_MANUAIS_POR_ITEM_PADRAO, calcular_tudo
from .leitor_logs import ler_logs


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera indicadores de desempenho de robôs RPA a partir dos logs.")
    parser.add_argument("--logs", type=Path, default=Path("exemplos/logs"))
    parser.add_argument("--saida", type=Path, default=Path("output/indicadores_rpa.xlsx"))
    parser.add_argument("--inicio", help="Data inicial (AAAA-MM-DD)")
    parser.add_argument("--fim", help="Data final inclusiva (AAAA-MM-DD)")
    parser.add_argument("--minutos-por-item", type=float, default=MINUTOS_MANUAIS_POR_ITEM_PADRAO,
                        help="Tempo manual médio por item, para estimar horas economizadas")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    leitura = ler_logs(args.logs, args.inicio, args.fim)
    tabelas = calcular_tudo(leitura.execucoes, args.minutos_por_item)
    gerar_planilha(leitura, tabelas, args.saida)

    geral = tabelas["Mensal_Geral"]
    print(f"Arquivos lidos: {leitura.arquivos} | execuções: {len(leitura.execucoes)} | "
          f"duplicatas removidas: {len(leitura.duplicatas)} | linhas inválidas: {leitura.linhas_invalidas}")
    print(tabelas["Mensal_Robo"][["periodo", "robo", "execucoes", "taxa_sucesso", "confiabilidade", "horas_economizadas"]]
          .tail(10).to_string(index=False))
    print(f"\nHoras economizadas no período: {geral['horas_economizadas'].sum():.1f} h → {args.saida}")


if __name__ == "__main__":
    main()
