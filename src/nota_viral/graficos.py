"""Figuras do projeto. A cor segue o grupo de canais nas duas primeiras; azul é sempre a medida principal."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from nota_viral.estilo import APAGADO, AQUA, AZUL, EIXO, ESTILO, LARANJA, TINTA, TINTA_SECUNDARIA, milhar, nova_figura, numero

GRUPOS = {"TikTok (3 canais)": AZUL, "YouTube · Games": LARANJA, "YouTube · Ciência e Negócios": AQUA}


def _grupo(tabela: pd.DataFrame) -> pd.Series:
    grupo = pd.Series("YouTube · Ciência e Negócios", index=tabela.index)
    grupo[tabela["plataforma"] == "tiktok"] = "TikTok (3 canais)"
    grupo[(tabela["plataforma"] == "youtube") & (tabela["nicho"] == "Games")] = "YouTube · Games"
    return grupo


def _eixo_de_views(eixo) -> None:
    eixo.set_major_formatter(FuncFormatter(lambda v, _: milhar(v - 1) if v >= 1 else ""))


def nota_x_views(tabela: pd.DataFrame, ingenua: float, dentro: float) -> Figure:
    """Dispersão da nota contra as views, com os canais separados por cor."""
    with plt.rc_context(ESTILO):
        fig, ax = nova_figura(
            "Nota mais alta acompanha mais views, mas cada canal joga numa faixa diferente",
            f"Cada ponto é um post. Correlação de postos: {numero(ingenua)} com tudo junto, {numero(dentro)} comparando só dentro do mesmo canal.",
        )
        fig.subplots_adjust(bottom=0.24)
        grupos = _grupo(tabela)
        for nome, cor in GRUPOS.items():
            recorte = tabela[grupos == nome]
            ax.plot(recorte["nota"], recorte["views"] + 1, "o", color=cor, label=nome, alpha=0.9)
        ax.set_yscale("log")
        ax.set_yticks([1, 11, 101, 1001])
        _eixo_de_views(ax.yaxis)
        ax.minorticks_off()
        ax.set_xlabel("nota de viralidade dada antes de publicar")
        ax.set_ylabel("views (escala logarítmica)")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: numero(v)))
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, fontsize=9)
        return fig


def views_por_canal(tabela: pd.DataFrame, resumo: pd.DataFrame) -> Figure:
    """Faixa de pontos: as views de cada post, canal por canal."""
    with plt.rc_context(ESTILO):
        fig, ax = nova_figura(
            "O canal decide a ordem de grandeza das views",
            "Views de cada post, por canal. O traço vertical é a mediana do canal.",
            altura=3.9,
        )
        fig.subplots_adjust(left=0.24, bottom=0.17)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        grupos = _grupo(tabela)
        gerador = np.random.default_rng(3)
        for y, canal in enumerate(resumo.index):
            recorte = tabela[tabela["canal"] == canal]
            cor = GRUPOS[grupos[recorte.index[0]]]
            desvio = gerador.uniform(-0.16, 0.16, len(recorte))
            ax.plot(recorte["views"] + 1, y + desvio, "o", color=cor, alpha=0.9, zorder=3)
            mediana = resumo.loc[canal, "views_mediana"]
            ax.plot([mediana + 1] * 2, [y - 0.32, y + 0.32], color=TINTA, linewidth=2, zorder=4)
            ax.annotate(milhar(mediana), (mediana + 1, y - 0.32), xytext=(0, 3), textcoords="offset points", ha="center", color=TINTA, fontsize=8.5)
        ax.set_xscale("log")
        ax.set_xticks([1, 11, 101, 1001])
        _eixo_de_views(ax.xaxis)
        ax.minorticks_off()
        ax.set_yticks(range(len(resumo)), list(resumo.index))
        ax.set_ylim(-0.6, len(resumo) - 0.4)
        ax.invert_yaxis()
        ax.set_xlabel("views (escala logarítmica)")
        return fig


def correlacoes(tabela: pd.DataFrame) -> Figure:
    """Ponto e intervalo de 95% da correlação em cada comparação."""
    with plt.rc_context(ESTILO):
        fig, ax = nova_figura(
            "O sinal aparece no conjunto, mas depende de quais posts entram na conta",
            "Correlação de postos entre nota e views, com intervalo de 95% (bootstrap reamostrando cortes).",
            altura=3.5,
        )
        fig.subplots_adjust(left=0.43, bottom=0.19, right=0.97)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        for y, (nome, linha) in enumerate(tabela.iterrows()):
            principal = nome == "Dentro de cada canal"
            cor = AZUL if principal else APAGADO
            ax.plot([linha["IC 95% inferior"], linha["IC 95% superior"]], [y, y], color=cor, linewidth=2, zorder=2)
            ax.plot(linha["correlação"], y, "o", color=cor, zorder=3)
            ax.annotate(
                f"{numero(linha['correlação'])}  [{numero(linha['IC 95% inferior'])} ; {numero(linha['IC 95% superior'])}]",
                (linha["IC 95% superior"], y), xytext=(8, 0), textcoords="offset points", va="center",
                color=TINTA if principal else TINTA_SECUNDARIA, fontsize=9, fontweight="bold" if principal else "normal",
            )
        ax.axvline(0, color=EIXO, linewidth=1.2, zorder=1)
        ax.annotate("sem relação", (0, -0.62), xytext=(4, 0), textcoords="offset points", color=APAGADO, fontsize=8.5, va="center")
        ax.set_yticks(range(len(tabela)), [f"{nome} (n = {int(n)})" for nome, n in zip(tabela.index, tabela["posts"])])
        ax.set_ylim(-0.85, len(tabela) - 0.5)
        ax.invert_yaxis()
        ax.set_xlim(-0.45, 1.6)
        ax.set_xticks([-0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: numero(v, 1)))
        ax.set_xlabel("correlação de postos (0 = sem relação, 1 = ordem perfeita)")
        return fig


def poder(curva: pd.DataFrame, marcos: list[tuple[str, int]], observada: float) -> Figure:
    """Menor correlação detectável em função do número de posts, com os marcos da agenda."""
    with plt.rc_context(ESTILO):
        hoje = float(np.interp(marcos[0][1], curva["posts"], curva["correlação detectável"]))
        fig, ax = nova_figura(
            f"Com a amostra de hoje, só uma correlação a partir de {numero(hoje)} seria detectada",
            "Menor correlação detectável com 80% de poder, conforme o número de posts com métricas.",
        )
        ax.plot(curva["posts"], curva["correlação detectável"], color=AZUL, zorder=3)
        ax.axhline(observada, color=EIXO, linewidth=1.2, zorder=1)
        ax.annotate(f"correlação observada dentro do canal: {numero(observada)}", (curva["posts"].max(), observada), xytext=(-4, 5), textcoords="offset points", ha="right", color=APAGADO, fontsize=8.5)
        # Posição de cada rótulo escolhida para não encostar na curva nem no vizinho.
        posicoes = [((7, 9), "left", "bottom"), ((0, 12), "center", "bottom"), ((0, -12), "center", "top"), ((0, 12), "right", "bottom")]
        for (rotulo, n), (deslocamento, horizontal, vertical) in zip(marcos, posicoes):
            detectavel = float(np.interp(n, curva["posts"], curva["correlação detectável"]))
            ax.plot(n, detectavel, "o", color=AZUL, zorder=4)
            ax.annotate(f"{rotulo}\n{milhar(n)} posts → {numero(detectavel)}", (n, detectavel), xytext=deslocamento, textcoords="offset points", color=TINTA_SECUNDARIA, fontsize=8.5, ha=horizontal, va=vertical)
        ax.set_xscale("log")
        ax.set_xticks([10, 30, 100, 300, 800])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: milhar(v)))
        ax.minorticks_off()
        ax.set_ylim(0, 0.9)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: numero(v, 1)))
        ax.set_xlabel("posts com métricas (escala logarítmica)")
        ax.set_ylabel("menor correlação detectável")
        return fig
