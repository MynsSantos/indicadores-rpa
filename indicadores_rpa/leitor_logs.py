"""Lê logs de execução de robôs (JSON Lines), valida e remove duplicidades."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

CAMPOS = ["id_execucao", "robo", "grupo", "inicio", "fim", "status", "itens_processados", "itens_com_erro"]
STATUS_VALIDOS = {"sucesso", "erro_negocio", "erro_sistema"}


@dataclass
class Leitura:
    execucoes: pd.DataFrame
    duplicatas: pd.DataFrame
    linhas_invalidas: int
    arquivos: int


def _ler_arquivo(caminho: Path) -> tuple[list[dict], int]:
    registros, invalidas = [], 0
    for n, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), start=1):
        if not linha.strip():
            continue
        try:
            reg = json.loads(linha)
            if not all(c in reg for c in CAMPOS) or reg["status"] not in STATUS_VALIDOS:
                raise ValueError("campos obrigatórios ausentes ou status inválido")
            reg["arquivo_origem"] = caminho.name
            registros.append(reg)
        except (json.JSONDecodeError, ValueError) as exc:
            invalidas += 1
            logger.debug("%s:%d ignorada (%s)", caminho.name, n, exc)
    return registros, invalidas


def ler_logs(pasta: Path, inicio: str | None = None, fim: str | None = None) -> Leitura:
    arquivos = sorted(pasta.glob("*.jsonl"))
    registros, invalidas = [], 0
    for arq in arquivos:
        regs, inv = _ler_arquivo(arq)
        registros += regs
        invalidas += inv

    df = pd.DataFrame(registros, columns=CAMPOS + ["mensagem", "arquivo_origem"])
    df["inicio"] = pd.to_datetime(df["inicio"])
    df["fim"] = pd.to_datetime(df["fim"])
    df["duracao_min"] = ((df["fim"] - df["inicio"]).dt.total_seconds() / 60).round(2)

    if inicio:
        df = df[df["inicio"] >= pd.Timestamp(inicio)]
    if fim:
        df = df[df["inicio"] < pd.Timestamp(fim) + pd.Timedelta(days=1)]  # data final inclusiva

    # O mesmo id_execucao pode aparecer em mais de um arquivo (reenvio de log, retry do orquestrador).
    # Mantemos o registro mais recente (maior "fim") e guardamos os descartados para auditoria.
    df = df.sort_values(["id_execucao", "fim"])
    duplicadas = df.duplicated("id_execucao", keep="last")
    return Leitura(
        execucoes=df[~duplicadas].reset_index(drop=True),
        duplicatas=df[duplicadas].reset_index(drop=True),
        linhas_invalidas=invalidas,
        arquivos=len(arquivos),
    )
