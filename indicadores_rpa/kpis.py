"""Calcula os indicadores de desempenho dos robôs por período e nível de agrupamento."""

from __future__ import annotations

import pandas as pd

# Tempo médio que uma pessoa levaria por item, usado para estimar horas economizadas.
MINUTOS_MANUAIS_POR_ITEM_PADRAO = 4.0

PERIODOS = {"Diario": "D", "Semanal": "W-SUN", "Mensal": "M"}  # semana de segunda a domingo
NIVEIS = {"Robo": ["robo"], "Grupo": ["grupo"], "Geral": []}


def classificar_confiabilidade(taxa_sucesso: float) -> str:
    if taxa_sucesso >= 0.95:
        return "Alta"
    if taxa_sucesso >= 0.80:
        return "Média"
    return "Baixa"


def agregar(df: pd.DataFrame, chaves: list[str], minutos_por_item: float = MINUTOS_MANUAIS_POR_ITEM_PADRAO) -> pd.DataFrame:
    g = df.groupby(chaves, dropna=False) if chaves else df.assign(_todos="Geral").groupby("_todos")
    out = g.agg(
        execucoes=("id_execucao", "count"),
        sucessos=("status", lambda s: (s == "sucesso").sum()),
        erros_negocio=("status", lambda s: (s == "erro_negocio").sum()),
        erros_sistema=("status", lambda s: (s == "erro_sistema").sum()),
        itens_processados=("itens_processados", "sum"),
        itens_com_erro=("itens_com_erro", "sum"),
        duracao_media_min=("duracao_min", "mean"),
        tempo_robo_h=("duracao_min", lambda s: s.sum() / 60),
    ).reset_index()
    if not chaves:
        out = out.drop(columns="_todos")

    out["taxa_sucesso"] = out["sucessos"] / out["execucoes"]
    # Erro de negócio (dado de entrada ruim) não é falha do robô: entra no cálculo separado.
    out["taxa_falha_tecnica"] = out["erros_sistema"] / out["execucoes"]
    # Itens que o robô concluiu × tempo que uma pessoa levaria em cada um.
    out["horas_economizadas"] = (out["itens_processados"] - out["itens_com_erro"]) * minutos_por_item / 60
    out["confiabilidade"] = (1 - out["taxa_falha_tecnica"]).map(classificar_confiabilidade)
    return out.round({"duracao_media_min": 2, "tempo_robo_h": 2, "taxa_sucesso": 4, "taxa_falha_tecnica": 4, "horas_economizadas": 1})


def calcular_tudo(execucoes: pd.DataFrame, minutos_por_item: float = MINUTOS_MANUAIS_POR_ITEM_PADRAO) -> dict[str, pd.DataFrame]:
    """Retorna {'Diario_Robo': df, 'Semanal_Grupo': df, ...} com todas as combinações."""
    tabelas = {}
    for nome_periodo, freq in PERIODOS.items():
        df = execucoes.assign(periodo=execucoes["inicio"].dt.to_period(freq).dt.start_time.dt.date)
        for nome_nivel, chaves in NIVEIS.items():
            tabelas[f"{nome_periodo}_{nome_nivel}"] = agregar(df, ["periodo"] + chaves, minutos_por_item)
    return tabelas
