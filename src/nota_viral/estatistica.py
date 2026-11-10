"""Ferramentas estatísticas: correlação dentro de grupos, permutação, bootstrap por corte, poder."""

from __future__ import annotations

from collections.abc import Callable
from math import atanh, ceil, tanh

import numpy as np
import pandas as pd
from scipy import stats


def postos_padronizados(valores: pd.Series, grupos: pd.Series) -> pd.Series:
    """Posto de cada valor dentro do seu grupo, centrado e em escala comum.

    Comparar postos dentro do grupo tira o efeito do grupo: um corte com muitas views para o
    padrão do seu canal fica alto mesmo que o canal inteiro tenha poucas views. Grupos com
    menos de 3 itens ou sem variação ficam de fora (viram NaN).
    """
    def padronizar(v: pd.Series) -> pd.Series:
        postos = v.rank()
        desvio = postos.std(ddof=0)
        if len(v) < 3 or desvio == 0:
            return pd.Series(np.nan, index=v.index)
        return (postos - postos.mean()) / desvio

    return valores.groupby(grupos, group_keys=False).apply(padronizar)


def correlacao_dentro_dos_grupos(x: pd.Series, y: pd.Series, grupos: pd.Series) -> float:
    """Correlação de postos entre x e y usando só a variação dentro de cada grupo."""
    px, py = postos_padronizados(x, grupos), postos_padronizados(y, grupos)
    validos = px.notna() & py.notna()
    if validos.sum() < 4:
        return float("nan")
    return float(np.corrcoef(px[validos], py[validos])[0, 1])


def p_por_permutacao(
    x: pd.Series, y: pd.Series, grupos: pd.Series, repeticoes: int = 5000, semente: int = 42
) -> float:
    """p-valor bicaudal: embaralha y dentro de cada grupo e vê com que frequência a correlação é tão forte."""
    observada = abs(correlacao_dentro_dos_grupos(x, y, grupos))
    gerador = np.random.default_rng(semente)
    indices = [np.flatnonzero(grupos.to_numpy() == g) for g in pd.unique(grupos)]
    valores = y.to_numpy().copy()
    extremos = 0
    for _ in range(repeticoes):
        embaralhado = valores.copy()
        for idx in indices:
            embaralhado[idx] = gerador.permutation(valores[idx])
        r = correlacao_dentro_dos_grupos(x, pd.Series(embaralhado, index=y.index), grupos)
        extremos += abs(r) >= observada - 1e-12
    return (extremos + 1) / (repeticoes + 1)


def bootstrap_por_corte(
    dados: pd.DataFrame, estatistica: Callable[[pd.DataFrame], float], repeticoes: int = 2000, semente: int = 42
) -> tuple[float, float]:
    """Intervalo de 95% reamostrando cortes inteiros.

    O mesmo corte aparece em mais de uma plataforma, então as linhas não são independentes:
    quem é sorteado é o corte, e ele traz todos os seus posts.
    """
    gerador = np.random.default_rng(semente)
    por_corte = {corte: grupo for corte, grupo in dados.groupby("corte")}
    cortes = np.array(list(por_corte))
    valores = []
    for _ in range(repeticoes):
        sorteados = gerador.choice(cortes, size=len(cortes), replace=True)
        amostra = pd.concat([por_corte[c] for c in sorteados], ignore_index=True)
        valor = estatistica(amostra)
        if np.isfinite(valor):
            valores.append(valor)
    return float(np.quantile(valores, 0.025)), float(np.quantile(valores, 0.975))


def amostra_para_detectar(correlacao: float, alfa: float = 0.05, poder: float = 0.80) -> int:
    """Quantos itens são precisos para detectar uma correlação desse tamanho (aproximação de Fisher)."""
    z = stats.norm.ppf(1 - alfa / 2) + stats.norm.ppf(poder)
    return ceil((z / atanh(correlacao)) ** 2 + 3)


def correlacao_detectavel(n: int, alfa: float = 0.05, poder: float = 0.80) -> float:
    """Menor correlação que uma amostra de n itens detecta com o poder dado."""
    if n <= 3:
        return float("nan")
    z = stats.norm.ppf(1 - alfa / 2) + stats.norm.ppf(poder)
    return float(tanh(z / np.sqrt(n - 3)))


def benjamini_hochberg(p_valores: pd.Series) -> pd.Series:
    """p-valores ajustados para a taxa de falsas descobertas (Benjamini-Hochberg)."""
    ordenados = p_valores.sort_values()
    m = len(ordenados)
    ajustados = (ordenados * m / np.arange(1, m + 1))[::-1].cummin()[::-1].clip(upper=1.0)
    return ajustados.reindex(p_valores.index)


def corrigir_restricao_de_faixa(correlacao: float, desvio_amostra: float, desvio_total: float) -> float:
    """Correção de Thorndike (caso 2): a correlação que se esperaria se a faixa da nota não fosse restrita.

    Só os cortes de nota mais alta são publicados, e medir numa faixa estreita encolhe a correlação.
    A correção supõe relação linear e a mesma dispersão dos erros fora da faixa observada.
    """
    k = desvio_total / desvio_amostra
    return float(correlacao * k / np.sqrt(1 - correlacao**2 + correlacao**2 * k**2))
