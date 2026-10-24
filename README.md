# Indicadores de Desempenho de Robôs RPA

Transforma os **logs de execução de robôs** em **KPIs de operação** (taxa de sucesso, falhas técnicas × erros de negócio, duração média, confiabilidade e **horas economizadas**) por dia, semana e mês, por robô, por área e no geral. Tudo numa planilha Excel com painel e gráfico.

> Projeto de portfólio inspirado na gestão de indicadores de um Centro de Excelência de automação em que atuo. Código escrito do zero, com logs **sintéticos**.

## O problema

Com dezenas de robôs rodando, perguntas como *"qual automação mais falha?"*, *"quanto tempo o RPA economizou este mês?"* ou *"esse erro foi do robô ou do dado de entrada?"* ficam sem resposta, ou dependem de alguém abrindo log por log.

## O que o projeto faz

- Lê todos os `*.jsonl` de uma pasta, **ignora linhas corrompidas** (e conta quantas foram)
- **Remove duplicatas**: quando o orquestrador reenvia o log de uma execução, mantém o registro mais recente e guarda os descartados numa aba de auditoria
- Separa **erro de sistema** (falha do robô) de **erro de negócio** (dado de entrada ruim), porque só o primeiro pesa na confiabilidade
- Estima **horas economizadas** = itens concluídos × minutos manuais por item (parâmetro configurável)
- Classifica a **confiabilidade**: Alta (≥ 95%), Média (≥ 80%) ou Baixa
- Gera 9 visões (`Diario|Semanal|Mensal` × `Robo|Grupo|Geral`) + painel com gráfico combinado

## Executando

```bash
pip install -r requirements.txt
python scripts/gerar_logs_sinteticos.py      # ~950 execuções de 5 robôs fictícios
python -m indicadores_rpa --logs exemplos/logs --saida output/indicadores_rpa.xlsx
```

```
Arquivos lidos: 20 | execuções: 936 | duplicatas removidas: 26 | linhas inválidas: 7
   periodo                     robo  execucoes  taxa_sucesso confiabilidade  horas_economizadas
2026-10-01     conciliacao_bancaria         24        0.9583           Alta               184.8
2026-10-01    download_comprovantes         36        0.7778          Média               132.1
2026-10-01 lancamento_notas_fiscais         48        0.8542          Média                99.7
...
Horas economizadas no período: 2921.3 h
```

> A confiabilidade considera só falhas técnicas (`erro_sistema`); por isso um robô pode ter taxa de sucesso de 82% e confiabilidade Alta: o restante foi erro do dado de entrada.

Opções: `--inicio 2026-08-01 --fim 2026-08-31` (datas inclusivas) e `--minutos-por-item 6`.

### Formato do log

Uma execução por linha (JSON Lines):

```json
{"id_execucao": "exec-0001", "robo": "conciliacao_bancaria", "grupo": "Financeiro",
 "inicio": "2026-10-01T08:00:00", "fim": "2026-10-01T08:18:00",
 "status": "sucesso | erro_negocio | erro_sistema",
 "itens_processados": 120, "itens_com_erro": 0, "mensagem": "..."}
```

Qualquer orquestrador (Power Automate, UiPath, scripts Python) pode gravar nesse formato com uma ação de "acrescentar ao arquivo".

## Estrutura

```
indicadores_rpa/
├── leitor_logs.py   # leitura, validação, filtro de período e deduplicação
├── kpis.py          # agregações e regras de confiabilidade/economia
├── excel.py         # planilha formatada, painel e gráfico (xlsxwriter)
└── __main__.py      # CLI
scripts/gerar_logs_sinteticos.py
```

## Testes

```bash
pytest
```

## Tecnologias

Python 3.10+ · pandas · xlsxwriter · pytest

---
Desenvolvido por **Yasmim Santos** · Licença MIT
