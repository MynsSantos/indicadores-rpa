import json

import pandas as pd
import pytest

from indicadores_rpa.excel import gerar_planilha
from indicadores_rpa.kpis import agregar, calcular_tudo, classificar_confiabilidade
from indicadores_rpa.leitor_logs import ler_logs


def _reg(id_, status="sucesso", inicio="2026-10-01T10:00:00", fim="2026-10-01T10:30:00", robo="robo_a", itens=10, erros=0):
    return {"id_execucao": id_, "robo": robo, "grupo": "G1", "inicio": inicio, "fim": fim,
            "status": status, "itens_processados": itens, "itens_com_erro": erros, "mensagem": ""}


@pytest.fixture
def pasta_logs(tmp_path):
    linhas = [
        _reg("1"),
        _reg("2", status="erro_sistema", inicio="2026-10-02T10:00:00", fim="2026-10-02T10:10:00"),
        _reg("3", status="erro_negocio", erros=2, inicio="2026-10-08T09:00:00", fim="2026-10-08T09:20:00"),
    ]
    (tmp_path / "a.jsonl").write_text("\n".join(json.dumps(l) for l in linhas) + "\n{quebrado\n", encoding="utf-8")
    # execução 1 reenviada em outro arquivo, com fim posterior → deve prevalecer
    (tmp_path / "b.jsonl").write_text(json.dumps(_reg("1", fim="2026-10-01T10:45:00")), encoding="utf-8")
    return tmp_path


def test_leitura_remove_duplicata_e_conta_invalidas(pasta_logs):
    leitura = ler_logs(pasta_logs)
    assert len(leitura.execucoes) == 3
    assert len(leitura.duplicatas) == 1
    assert leitura.linhas_invalidas == 1
    exec1 = leitura.execucoes.set_index("id_execucao").loc["1"]
    assert exec1["duracao_min"] == 45  # manteve o registro mais recente


def test_filtro_de_periodo_inclusivo(pasta_logs):
    assert len(ler_logs(pasta_logs, inicio="2026-10-02", fim="2026-10-02").execucoes) == 1


def test_kpis_gerais(pasta_logs):
    geral = agregar(ler_logs(pasta_logs).execucoes, [])
    linha = geral.iloc[0]
    assert linha["execucoes"] == 3
    assert linha["taxa_sucesso"] == pytest.approx(1 / 3, abs=1e-4)
    assert linha["taxa_falha_tecnica"] == pytest.approx(1 / 3, abs=1e-4)
    # (30 itens - 2 com erro) × 4 min / 60
    assert linha["horas_economizadas"] == pytest.approx(1.9, abs=0.05)


@pytest.mark.parametrize("taxa,esperado", [(0.99, "Alta"), (0.9, "Média"), (0.5, "Baixa")])
def test_confiabilidade(taxa, esperado):
    assert classificar_confiabilidade(taxa) == esperado


def test_semanas_comecam_na_segunda(pasta_logs):
    semanal = calcular_tudo(ler_logs(pasta_logs).execucoes)["Semanal_Geral"]
    assert [str(p) for p in semanal["periodo"]] == ["2026-09-28", "2026-10-05"]


def test_planilha_completa(pasta_logs, tmp_path):
    leitura = ler_logs(pasta_logs)
    destino = gerar_planilha(leitura, calcular_tudo(leitura.execucoes), tmp_path / "out.xlsx")
    abas = pd.ExcelFile(destino).sheet_names
    assert abas[0] == "Painel"
    assert {"Execucoes", "Diario_Robo", "Semanal_Grupo", "Mensal_Geral", "Duplicatas_Removidas"} <= set(abas)


def test_logs_sinteticos():
    from scripts.gerar_logs_sinteticos import PASTA, gerar

    gerar()
    leitura = ler_logs(PASTA)
    assert len(leitura.execucoes) > 500 and len(leitura.duplicatas) > 0
