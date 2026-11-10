"""Orquestra a análise. Cada função devolve uma tabela usada no notebook e no README."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from nota_viral import estatistica as est
from nota_viral.dados import CRITERIOS, NICHOS_ATIVOS, NOME_DO_CRITERIO


def resumo_da_amostra(cortes: pd.DataFrame, tabela: pd.DataFrame, posts: pd.DataFrame) -> dict:
    """Tamanho de cada conjunto: o que foi pontuado, o que foi publicado e o que já tem métrica."""
    return {
        "cortes_pontuados": int(len(cortes)),
        "posts_com_metricas": int(len(tabela)),
        "cortes_publicados": int(tabela["corte"].nunique()),
        "coletas": int(posts["coleta"].nunique()),
        "coleta_usada": str(tabela["coleta"].iloc[0]),
        "horas_no_ar_mediana": float(tabela["horas_no_ar"].median()),
    }


def views_por_canal(tabela: pd.DataFrame) -> pd.DataFrame:
    """Audiência de cada canal: é o que mais explica as views de um post."""
    resumo = tabela.groupby("canal").agg(
        posts=("views", "size"),
        views_mediana=("views", "median"),
        views_minimo=("views", "min"),
        views_maximo=("views", "max"),
        nota_mediana=("nota", "median"),
    )
    return resumo.sort_values("views_mediana", ascending=False)


def _spearman(tabela: pd.DataFrame, coluna: str = "nota") -> float:
    return float(stats.spearmanr(tabela[coluna], tabela["views"]).statistic)


def _dentro_do_canal(tabela: pd.DataFrame, coluna: str = "nota") -> float:
    return est.correlacao_dentro_dos_grupos(tabela[coluna], tabela["views"], tabela["canal"])


def correlacoes(tabela: pd.DataFrame, repeticoes: int = 2000) -> pd.DataFrame:
    """A mesma pergunta respondida de três jeitos: tudo junto, por plataforma e dentro de cada canal."""
    linhas = []

    def linha(nome: str, recorte: pd.DataFrame, funcao, p_valor: float) -> None:
        inferior, superior = est.bootstrap_por_corte(recorte, funcao, repeticoes)
        linhas.append(
            {
                "comparação": nome,
                "posts": len(recorte),
                "correlação": funcao(recorte),
                "IC 95% inferior": inferior,
                "IC 95% superior": superior,
                "p": p_valor,
            }
        )

    linha("Tudo junto (ingênua)", tabela, _spearman, float(stats.spearmanr(tabela["nota"], tabela["views"]).pvalue))
    recortes = {
        "Dentro de cada canal": tabela,
        "Dentro do canal, posts com mais de 24 h": tabela[tabela["horas_no_ar"] >= 24],
        "Dentro do canal, posts com menos de 24 h": tabela[tabela["horas_no_ar"] < 24],
    }
    for nome, recorte in recortes.items():
        p_valor = est.p_por_permutacao(recorte["nota"], recorte["views"], recorte["canal"], repeticoes=3000)
        linha(nome, recorte, _dentro_do_canal, p_valor)
    return pd.DataFrame(linhas).set_index("comparação")


def correlacao_por_canal(tabela: pd.DataFrame) -> pd.DataFrame:
    """Correlação de postos entre nota e views em cada canal, separadamente (amostras muito pequenas)."""
    linhas = []
    for canal, recorte in tabela.groupby("canal"):
        resultado = stats.spearmanr(recorte["nota"], recorte["views"])
        linhas.append({"canal": canal, "posts": len(recorte), "correlação": resultado.statistic, "p": resultado.pvalue})
    return pd.DataFrame(linhas).set_index("canal")


def componentes_da_nota(tabela: pd.DataFrame) -> pd.DataFrame:
    """Qual parte da nota (juiz, métricas do vídeo de origem, cada critério) acompanha as views dentro do canal.

    São 10 testes na mesma amostra, então os p-valores são ajustados por Benjamini-Hochberg.
    """
    nomes = {"nota_juiz": "nota do juiz de IA", "nota_metricas": "nota das métricas do vídeo de origem", **NOME_DO_CRITERIO}
    linhas = []
    for coluna in ["nota_juiz", "nota_metricas", *CRITERIOS]:
        validos = tabela.dropna(subset=[coluna])
        linhas.append(
            {
                "componente": nomes[coluna],
                "correlação ingênua": _spearman(validos, coluna),
                "correlação dentro do canal": _dentro_do_canal(validos, coluna),
                "p": est.p_por_permutacao(validos[coluna], validos["views"], validos["canal"], repeticoes=2000),
            }
        )
    resultado = pd.DataFrame(linhas).set_index("componente")
    resultado["p ajustado"] = est.benjamini_hochberg(resultado["p"])
    return resultado.sort_values("p")


def checagens(tabela: pd.DataFrame, repeticoes: int = 2000) -> pd.DataFrame:
    """A correlação dentro do canal muda quando se troca o recorte ou a unidade de análise?"""
    linhas = []

    def linha(nome: str, recorte: pd.DataFrame) -> None:
        inferior, superior = est.bootstrap_por_corte(recorte, _dentro_do_canal, repeticoes)
        linhas.append(
            {
                "checagem": nome,
                "posts": len(recorte),
                "correlação dentro do canal": _dentro_do_canal(recorte),
                "IC 95% inferior": inferior,
                "IC 95% superior": superior,
            }
        )

    linha("Todos os posts", tabela)
    linha("Sem o post de mais views de cada canal", tabela[tabela["views"] < tabela.groupby("canal")["views"].transform("max")])
    # Comparar só posts do mesmo canal publicados no mesmo dia tira o efeito do lote do dia.
    mesmo_dia = tabela.assign(canal=tabela["canal"] + " · " + tabela["publicado_em"].str[:10])
    linha("Dentro do canal e do dia de publicação", mesmo_dia)
    return pd.DataFrame(linhas).set_index("checagem")


def views_por_idade(tabela: pd.DataFrame) -> pd.DataFrame:
    """Views e nota por plataforma e idade do post: o lote mais recente se comporta como os anteriores?"""
    faixas = pd.cut(tabela["horas_no_ar"], [0, 24, 48, 1000], labels=["menos de 24 h", "24 a 48 h", "mais de 48 h"])
    return tabela.groupby(["plataforma", faixas], observed=True).agg(
        posts=("views", "size"), views_mediana=("views", "median"), nota_mediana=("nota", "median")
    )


def ganho_da_nota_alta(tabela: pd.DataFrame, repeticoes: int = 2000) -> dict:
    """Em views: quanto rendem os cortes de nota acima da mediana do canal, em relação aos de nota abaixo.

    As views de cada post são divididas pela mediana do seu canal, para canais grandes e
    pequenos pesarem igual. O resultado é a razão entre as medianas dos dois grupos.
    """
    def razao(recorte: pd.DataFrame) -> float:
        relativa = recorte["views"] / recorte.groupby("canal")["views"].transform("median").clip(lower=1)
        alta = recorte["nota"] > recorte.groupby("canal")["nota"].transform("median")
        if alta.sum() < 3 or (~alta).sum() < 3 or relativa[~alta].median() == 0:
            return float("nan")
        return float(relativa[alta].median() / relativa[~alta].median())

    inferior, superior = est.bootstrap_por_corte(tabela, razao, repeticoes)
    return {"razao_de_views": razao(tabela), "ic95_inferior": inferior, "ic95_superior": superior}


def limiar_de_aprovacao(cortes: pd.DataFrame, limiar: float = 0.80) -> dict:
    """O pipeline aprova cortes com nota a partir de 0,80. Quantos chegam lá?"""
    return {
        "limiar": limiar,
        "nota_maxima": float(cortes["nota"].max()),
        "cortes_no_limiar": int((cortes["nota"] >= limiar).sum()),
        "cortes_acima_de_0_70": int((cortes["nota"] >= 0.70).sum()),
        "total": int(len(cortes)),
    }


def nota_por_nicho(cortes: pd.DataFrame) -> pd.DataFrame:
    """A nota já carrega o nicho: alguns nichos recebem notas sistematicamente mais altas."""
    ativos = cortes[cortes["nicho"].isin(NICHOS_ATIVOS)]
    return ativos.groupby("nicho")["nota"].agg(cortes="size", mediana="median", p25=lambda v: v.quantile(0.25), p75=lambda v: v.quantile(0.75))


def restricao_de_faixa(cortes: pd.DataFrame, tabela: pd.DataFrame, correlacao: float) -> dict:
    """Só os cortes de nota mais alta vão ao ar: a faixa observada é mais estreita que a pontuada."""
    publicados = tabela.drop_duplicates("corte")
    desvio_total, desvio_amostra = float(cortes["nota"].std()), float(publicados["nota"].std())
    return {
        "nota_p10_todos": float(cortes["nota"].quantile(0.10)),
        "nota_p90_todos": float(cortes["nota"].quantile(0.90)),
        "nota_p10_publicados": float(publicados["nota"].quantile(0.10)),
        "nota_p90_publicados": float(publicados["nota"].quantile(0.90)),
        "desvio_todos": desvio_total,
        "desvio_publicados": desvio_amostra,
        "correlacao_observada": correlacao,
        "correlacao_corrigida": est.corrigir_restricao_de_faixa(correlacao, desvio_amostra, desvio_total),
    }


def crescimento_entre_coletas(posts: pd.DataFrame) -> pd.DataFrame | None:
    """Quanto as views crescem de uma coleta para a seguinte: as views chegam no primeiro dia ou continuam?"""
    coletas = sorted(posts["coleta"].unique())
    if len(coletas) < 2:
        return None
    antes, depois = coletas[-2], coletas[-1]
    pares = posts[posts["coleta"] == antes].merge(
        posts[posts["coleta"] == depois], on=["corte", "plataforma"], suffixes=("_antes", "_depois")
    )
    pares["ganho"] = pares["views_depois"] - pares["views_antes"]
    pares["ganho_relativo"] = pares["ganho"] / pares["views_antes"].clip(lower=1)
    pares["mais_de_um_dia"] = pares["horas_no_ar_antes"] >= 24
    resumo = pares.groupby(["plataforma", "mais_de_um_dia"]).agg(
        posts=("ganho", "size"), ganho_mediano=("ganho", "median"), ganho_relativo_mediano=("ganho_relativo", "median")
    )
    resumo.attrs["coletas"] = (antes, depois)
    return resumo


def plano_de_amostra(tabela: pd.DataFrame, agenda: pd.DataFrame, alvos: tuple[float, ...] = (0.5, 0.4, 0.3, 0.2)) -> pd.DataFrame:
    """Quantos posts são precisos para detectar cada tamanho de correlação, e em que semana a agenda chega lá.

    Conta posts acumulados a partir da agenda já programada; supõe que todos vão ao ar e têm métrica coletada.
    """
    acumulado = (agenda["tiktok"] + agenda["youtube"]).cumsum()
    linhas = []
    for correlacao in alvos:
        necessario = est.amostra_para_detectar(correlacao)
        atingidas = agenda.loc[acumulado >= necessario, "semana"]
        linhas.append(
            {
                "correlação a detectar": correlacao,
                "posts necessários": necessario,
                "semana em que a agenda chega lá": atingidas.iloc[0] if len(atingidas) else "além da agenda",
            }
        )
    plano = pd.DataFrame(linhas).set_index("correlação a detectar")
    plano.attrs["posts_hoje"] = int(len(tabela))
    plano.attrs["detectavel_hoje"] = est.correlacao_detectavel(len(tabela))
    plano.attrs["detectavel_por_cortes"] = est.correlacao_detectavel(int(tabela["corte"].nunique()))
    return plano


def marcos_da_agenda(agenda: pd.DataFrame, posts_hoje: int) -> list[tuple[str, int]]:
    """Tamanho da amostra hoje e o que a agenda programada soma no fim de novembro, de dezembro e no total."""
    acumulado = (agenda["tiktok"] + agenda["youtube"]).cumsum()
    marcos = [("hoje", posts_hoje)]
    for rotulo, limite in [("fim de novembro", "2026-11-30"), ("fim de dezembro", "2026-12-28")]:
        ate = acumulado[agenda["semana"] <= limite]
        if len(ate):
            marcos.append((rotulo, int(ate.iloc[-1])))
    marcos.append(("fim da agenda", int(acumulado.iloc[-1])))
    return marcos


def curva_de_poder(maximo: int = 800) -> pd.DataFrame:
    """Menor correlação detectável (80% de poder) para cada tamanho de amostra."""
    tamanhos = np.unique(np.round(np.geomspace(10, maximo, 60)).astype(int))
    return pd.DataFrame({"posts": tamanhos, "correlação detectável": [est.correlacao_detectavel(int(n)) for n in tamanhos]})
