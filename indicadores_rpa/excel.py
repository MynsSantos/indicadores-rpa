"""Gera a planilha de indicadores, com um painel e um gráfico de evolução mensal."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .leitor_logs import Leitura

PERCENTUAIS = {"taxa_sucesso", "taxa_falha_tecnica"}


def _formatar(writer, aba: str, df: pd.DataFrame) -> None:
    book, ws = writer.book, writer.sheets[aba]
    cab = book.add_format({"bold": True, "bg_color": "#1F4E78", "font_color": "white"})
    pct = book.add_format({"num_format": "0.0%"})
    data = book.add_format({"num_format": "dd/mm/yyyy"})
    for i, col in enumerate(df.columns):
        ws.write(0, i, col, cab)
        fmt = pct if col in PERCENTUAIS else data if col == "periodo" else None
        ws.set_column(i, i, max(12, len(col) + 2), fmt)
    ws.freeze_panes(1, 0)
    if len(df):
        ws.autofilter(0, 0, len(df), len(df.columns) - 1)


def _painel(writer, leitura: Leitura, mensal_geral: pd.DataFrame, mensal_robo: pd.DataFrame) -> None:
    book = writer.book
    ws = book.add_worksheet("Painel")
    writer.sheets["Painel"] = ws
    titulo = book.add_format({"bold": True, "font_size": 16})
    rotulo = book.add_format({"bold": True})
    ex = leitura.execucoes

    ws.write("A1", "Indicadores de Automação (RPA)", titulo)
    linhas = [
        ("Período", f"{ex['inicio'].min():%d/%m/%Y} a {ex['inicio'].max():%d/%m/%Y}" if len(ex) else "-"),
        ("Execuções válidas", len(ex)),
        ("Duplicatas removidas", len(leitura.duplicatas)),
        ("Linhas de log inválidas", leitura.linhas_invalidas),
        ("Taxa de sucesso", float((ex["status"] == "sucesso").mean()) if len(ex) else "-"),
        ("Horas economizadas (estimativa)", round(float(mensal_geral["horas_economizadas"].sum()), 1)),
    ]
    pct = book.add_format({"num_format": "0.0%", "align": "right"})
    direita = book.add_format({"align": "right"})
    for i, (k, v) in enumerate(linhas, start=2):
        ws.write(i, 0, k, rotulo)
        ws.write(i, 1, v, pct if k == "Taxa de sucesso" else direita)
    ws.set_column(0, 0, 34)
    ws.set_column(1, 1, 26)

    n = len(mensal_geral)
    if n:
        grafico = book.add_chart({"type": "column"})
        grafico.add_series({
            "name": "Horas economizadas",
            "categories": ["Mensal_Geral", 1, 0, n, 0],
            "values": ["Mensal_Geral", 1, mensal_geral.columns.get_loc("horas_economizadas"), n,
                       mensal_geral.columns.get_loc("horas_economizadas")],
        })
        linha = book.add_chart({"type": "line"})
        linha.add_series({
            "name": "Taxa de sucesso",
            "categories": ["Mensal_Geral", 1, 0, n, 0],
            "values": ["Mensal_Geral", 1, mensal_geral.columns.get_loc("taxa_sucesso"), n,
                       mensal_geral.columns.get_loc("taxa_sucesso")],
            "y2_axis": True,
            "marker": {"type": "circle"},
        })
        grafico.combine(linha)
        grafico.set_title({"name": "Evolução mensal"})
        grafico.set_x_axis({"num_format": "mmm/yy"})
        grafico.set_y_axis({"name": "Horas"})
        linha.set_y2_axis({"name": "Sucesso", "num_format": "0%"})
        grafico.set_size({"width": 720, "height": 360})
        ws.insert_chart("D2", grafico)


def gerar_planilha(leitura: Leitura, tabelas: dict[str, pd.DataFrame], destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(destino, engine="xlsxwriter") as writer:
        abas = {"Execucoes": leitura.execucoes, **tabelas, "Duplicatas_Removidas": leitura.duplicatas}
        for nome, df in abas.items():
            df.to_excel(writer, sheet_name=nome, index=False)
            _formatar(writer, nome, df)
        _painel(writer, leitura, tabelas["Mensal_Geral"], tabelas["Mensal_Robo"])
        writer.book.worksheets_objs.insert(0, writer.book.worksheets_objs.pop())  # Painel como 1ª aba
        writer.sheets["Painel"].activate()
    return destino
