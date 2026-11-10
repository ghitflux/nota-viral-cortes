"""Carga dos extratos anonimizados de data/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DADOS = Path("data")
CRITERIOS = ["hook_3s", "standalone", "complete_arc", "shareability", "emotion", "energy", "insight", "humour"]
NOME_DO_CRITERIO = {
    "hook_3s": "gancho nos 3 primeiros segundos",
    "standalone": "faz sentido sozinho",
    "complete_arc": "começo, meio e fim",
    "shareability": "dá vontade de compartilhar",
    "emotion": "emoção",
    "energy": "energia",
    "insight": "ensina algo",
    "humour": "humor",
}
NICHOS_ATIVOS = ["Ciência", "Negócios", "Games"]


def carregar_cortes(pasta: Path = DADOS) -> pd.DataFrame:
    """Todos os cortes pontuados antes de publicar (publicados ou não)."""
    return pd.read_csv(pasta / "cortes_pontuados.csv")


def carregar_posts(pasta: Path = DADOS) -> pd.DataFrame:
    """Uma linha por post e por coleta de métricas."""
    return pd.read_csv(pasta / "posts_metricas.csv")


def carregar_agenda(pasta: Path = DADOS) -> pd.DataFrame:
    """Posts agendados por semana (para projetar quando a amostra fica suficiente)."""
    return pd.read_csv(pasta / "agenda_semanal.csv")


def juntar(cortes: pd.DataFrame, posts: pd.DataFrame, coleta: str | None = None) -> pd.DataFrame:
    """Posts de uma coleta (a mais recente, por padrão) com a nota e os critérios de cada corte.

    `canal` é a combinação de plataforma e nicho: cada canal tem a sua audiência, e é dentro
    dele que faz sentido comparar um corte com outro.
    """
    coleta = coleta or posts["coleta"].max()
    recorte = posts[posts["coleta"] == coleta]
    tabela = recorte.merge(cortes.drop(columns=["nicho"]), on="corte", how="inner")
    tabela["canal"] = tabela["plataforma"].str.capitalize().replace({"Tiktok": "TikTok", "Youtube": "YouTube"}) + " · " + tabela["nicho"]
    return tabela.reset_index(drop=True)
