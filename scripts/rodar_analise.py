"""Roda a análise completa e grava reports/resultados.json e as figuras do README."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from nota_viral import analise, dados, graficos, site

SAIDA = Path("reports")
FIGURAS = SAIDA / "figuras"


def _json(tabela: pd.DataFrame, orient: str = "index"):
    return json.loads(tabela.to_json(orient=orient, force_ascii=False))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    FIGURAS.mkdir(parents=True, exist_ok=True)

    cortes, posts, agenda = dados.carregar_cortes(), dados.carregar_posts(), dados.carregar_agenda()
    tabela = dados.juntar(cortes, posts)

    resumo = analise.resumo_da_amostra(cortes, tabela, posts)
    canais = analise.views_por_canal(tabela)
    correlacoes = analise.correlacoes(tabela)
    por_canal = analise.correlacao_por_canal(tabela)
    checagens = analise.checagens(tabela)
    idade = analise.views_por_idade(tabela)
    ganho = analise.ganho_da_nota_alta(tabela)
    componentes = analise.componentes_da_nota(tabela)
    nichos = analise.nota_por_nicho(cortes)
    dentro = float(correlacoes.loc["Dentro de cada canal", "correlação"])
    ingenua = float(correlacoes.loc["Tudo junto (ingênua)", "correlação"])
    faixa = analise.restricao_de_faixa(cortes, tabela, dentro)
    limiar = analise.limiar_de_aprovacao(cortes)
    crescimento = analise.crescimento_entre_coletas(posts)
    plano = analise.plano_de_amostra(tabela, agenda)
    curva = analise.curva_de_poder(max(1100, int((agenda["tiktok"] + agenda["youtube"]).sum()) + 50))
    marcos = analise.marcos_da_agenda(agenda, len(tabela))

    figuras = {
        "nota_x_views": graficos.nota_x_views(tabela, ingenua, dentro),
        "views_por_canal": graficos.views_por_canal(tabela, canais),
        "correlacoes": graficos.correlacoes(correlacoes),
        "poder": graficos.poder(curva, marcos, dentro),
    }
    for nome, figura in figuras.items():
        figura.savefig(FIGURAS / f"{nome}.png")
        plt.close(figura)

    resultados = {
        "amostra": resumo,
        "views_por_canal": _json(canais),
        "correlacoes": _json(correlacoes),
        "correlacao_por_canal": _json(por_canal),
        "checagens": _json(checagens),
        "views_por_idade": json.loads(idade.reset_index().to_json(orient="records", force_ascii=False)),
        "ganho_da_nota_alta": ganho,
        "componentes_da_nota": _json(componentes),
        "nota_por_nicho": _json(nichos),
        "restricao_de_faixa": faixa,
        "limiar_de_aprovacao": limiar,
        "crescimento_entre_coletas": None if crescimento is None else json.loads(crescimento.reset_index().to_json(orient="records", force_ascii=False)),
        "plano_de_amostra": {**plano.attrs, "tabela": _json(plano)},
        "marcos_da_agenda": [{"marco": m, "posts": n} for m, n in marcos],
        "curva_de_poder": _json(curva.round(4), "records"),
        "pontos": json.loads(
            tabela[["canal", "plataforma", "nicho", "nota", "views", "curtidas", "horas_no_ar"]].to_json(orient="records", force_ascii=False)
        ),
    }
    # O texto e o gráfico principal do site vêm de outro arquivo; daqui saem só os gráficos extras, calculados a
    # partir do próprio dicionário de resultados (passado por JSON para usar exatamente os números gravados).
    gravados = json.loads(json.dumps(resultados, ensure_ascii=False, default=float))
    resultados["para_o_site"] = {"graficos_extras": site.graficos_extras(gravados)}
    (SAIDA / "resultados.json").write_text(json.dumps(resultados, indent=2, ensure_ascii=False, default=float), encoding="utf-8")

    pd.set_option("display.width", 220)
    pd.set_option("display.float_format", lambda v: f"{v:.3f}")
    print(resumo)
    print(correlacoes.to_string())
    print(checagens.to_string())
    print(idade.to_string())
    print(por_canal.to_string())
    print(componentes.to_string())
    print("faixa:", faixa)
    print("plano:", plano.attrs)
    print(plano.to_string())
    print(crescimento.to_string() if crescimento is not None else "uma coleta só")
    print("ganho da nota alta:", ganho)
    print("limiar:", limiar)
    print("marcos:", marcos)
    print(f"Gravado em {SAIDA / 'resultados.json'} e {FIGURAS}")


if __name__ == "__main__":
    main()
