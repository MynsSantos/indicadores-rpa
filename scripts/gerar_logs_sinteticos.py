"""Gera logs SINTÉTICOS de robôs em exemplos/logs/ (um .jsonl por robô e mês).

Inclui de propósito: duplicatas (mesma execução registrada duas vezes),
linhas corrompidas e robôs com perfis de estabilidade diferentes.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

PASTA = Path(__file__).resolve().parents[1] / "exemplos" / "logs"

# robô: (grupo, execuções por dia útil, prob. erro sistema, prob. erro negócio, itens médios, minutos médios)
ROBOS = {
    "conciliacao_bancaria": ("Financeiro", 2, 0.02, 0.05, 120, 18),
    "lancamento_notas_fiscais": ("Contabil", 4, 0.06, 0.08, 35, 25),
    "download_comprovantes": ("Financeiro", 3, 0.15, 0.02, 60, 12),
    "relatorio_fechamento": ("Contabil", 1, 0.01, 0.01, 10, 40),
    "cadastro_fornecedores": ("Compras", 2, 0.04, 0.12, 15, 9),
}

MENSAGENS = {
    "sucesso": "Execução concluída",
    "erro_negocio": "Documento de entrada com dados incompletos",
    "erro_sistema": "Timeout ao acessar o sistema de destino",
}


def gerar(semente: int = 7, inicio=datetime(2026, 7, 1), dias: int = 110) -> list[Path]:
    rnd = random.Random(semente)
    PASTA.mkdir(parents=True, exist_ok=True)
    for antigo in PASTA.glob("*.jsonl"):
        antigo.unlink()

    arquivos: dict[Path, list[str]] = {}
    for robo, (grupo, por_dia, p_sis, p_neg, itens, minutos) in ROBOS.items():
        for d in range(dias):
            dia = inicio + timedelta(days=d)
            if dia.weekday() >= 5:
                continue
            for _ in range(por_dia):
                ini = dia.replace(hour=rnd.randint(6, 18), minute=rnd.randint(0, 59))
                sorteio = rnd.random()
                status = "erro_sistema" if sorteio < p_sis else "erro_negocio" if sorteio < p_sis + p_neg else "sucesso"
                n_itens = max(1, int(rnd.gauss(itens, itens * 0.2)))
                reg = {
                    "id_execucao": f"exec-{robo[:4]}-{rnd.getrandbits(40):010x}",
                    "robo": robo,
                    "grupo": grupo,
                    "inicio": ini.isoformat(),
                    "fim": (ini + timedelta(minutes=max(1, rnd.gauss(minutos, minutos * 0.25)))).isoformat(),
                    "status": status,
                    "itens_processados": n_itens if status != "erro_sistema" else rnd.randint(0, n_itens // 2),
                    "itens_com_erro": rnd.randint(1, 3) if status == "erro_negocio" else 0,
                    "mensagem": MENSAGENS[status],
                }
                arq = PASTA / f"{robo}_{ini:%Y-%m}.jsonl"
                linhas = arquivos.setdefault(arq, [])
                linhas.append(json.dumps(reg, ensure_ascii=False))
                if rnd.random() < 0.03:  # log reenviado pelo orquestrador
                    linhas.append(json.dumps(reg, ensure_ascii=False))
                if rnd.random() < 0.005:
                    linhas.append('{"id_execucao": "corrompido", "robo": ')

    for arq, linhas in arquivos.items():
        arq.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return list(arquivos)


if __name__ == "__main__":
    print(f"{len(gerar())} arquivos de log gerados em {PASTA}")
