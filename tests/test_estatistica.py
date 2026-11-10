import numpy as np
import pandas as pd
import pytest

from nota_viral import estatistica as est


def _dois_grupos(n: int = 200, semente: int = 0, efeito: float = 0.0) -> pd.DataFrame:
    """Dois canais com audiências muito diferentes; `efeito` liga a nota às views dentro do canal."""
    gerador = np.random.default_rng(semente)
    grupo = np.repeat(["pequeno", "grande"], n)
    nota = np.concatenate([gerador.normal(0.5, 0.1, n), gerador.normal(0.7, 0.1, n)])  # o canal grande recebe nota maior
    base = np.where(grupo == "grande", 1000.0, 10.0)
    views = base * np.exp(efeito * (nota - np.where(grupo == "grande", 0.7, 0.5)) / 0.1 + gerador.normal(0, 0.5, 2 * n))
    return pd.DataFrame({"corte": np.arange(2 * n), "canal": grupo, "nota": nota, "views": views})


def test_correlacao_dentro_dos_grupos_ignora_a_diferenca_entre_canais():
    dados = _dois_grupos(efeito=0.0)
    ingenua = np.corrcoef(dados["nota"].rank(), dados["views"].rank())[0, 1]
    dentro = est.correlacao_dentro_dos_grupos(dados["nota"], dados["views"], dados["canal"])
    assert ingenua > 0.5  # tudo junto parece haver relação: é só o canal
    assert abs(dentro) < 0.12  # dentro do canal, não há


def test_correlacao_dentro_dos_grupos_encontra_relacao_real():
    dados = _dois_grupos(efeito=0.6)
    assert est.correlacao_dentro_dos_grupos(dados["nota"], dados["views"], dados["canal"]) > 0.5


def test_postos_padronizados_descartam_grupo_pequeno_ou_constante():
    valores = pd.Series([1.0, 2.0, 3.0, 5.0, 5.0, 5.0, 9.0, 8.0])
    grupos = pd.Series(["a", "a", "a", "b", "b", "b", "c", "c"])
    postos = est.postos_padronizados(valores, grupos)
    assert postos[grupos == "a"].notna().all()
    assert postos[grupos == "b"].isna().all()  # sem variação
    assert postos[grupos == "c"].isna().all()  # menos de 3 itens
    assert postos[grupos == "a"].mean() == pytest.approx(0.0)


def test_permutacao_da_p_alto_sem_relacao_e_baixo_com_relacao():
    nula = _dois_grupos(n=60, efeito=0.0, semente=1)
    real = _dois_grupos(n=60, efeito=0.6, semente=1)
    assert est.p_por_permutacao(nula["nota"], nula["views"], nula["canal"], repeticoes=400) > 0.05
    assert est.p_por_permutacao(real["nota"], real["views"], real["canal"], repeticoes=400) < 0.01


def test_bootstrap_por_corte_contem_a_estimativa_e_mantem_os_posts_do_corte_juntos():
    dados = _dois_grupos(n=40, efeito=0.6, semente=2)
    dados["corte"] = np.tile(np.arange(40), 2)  # cada corte aparece nos dois canais

    def estatistica(amostra: pd.DataFrame) -> float:
        assert (amostra.groupby("corte").size() % 2 == 0).all()  # sempre os dois posts do corte
        return est.correlacao_dentro_dos_grupos(amostra["nota"], amostra["views"], amostra["canal"])

    inferior, superior = est.bootstrap_por_corte(dados, estatistica, repeticoes=200)
    assert inferior < estatistica(dados) < superior


def test_amostra_para_detectar_bate_com_valores_de_referencia():
    assert est.amostra_para_detectar(0.3) == 85
    assert est.amostra_para_detectar(0.2) == 194
    assert est.amostra_para_detectar(0.5) == 30


def test_correlacao_detectavel_e_o_inverso_da_amostra():
    for n in (30, 85, 194):
        assert est.amostra_para_detectar(est.correlacao_detectavel(n) + 1e-6) <= n
    assert est.correlacao_detectavel(64) > est.correlacao_detectavel(248)
    assert np.isnan(est.correlacao_detectavel(3))


def test_benjamini_hochberg_exemplo_conhecido():
    p = pd.Series([0.01, 0.04, 0.03, 0.20], index=list("abcd"))
    ajustado = est.benjamini_hochberg(p)
    assert ajustado["a"] == pytest.approx(0.04)
    assert ajustado["c"] == pytest.approx(0.0533, abs=1e-3)
    assert ajustado["b"] == pytest.approx(0.0533, abs=1e-3)
    assert ajustado["d"] == pytest.approx(0.20)
    assert (ajustado >= p).all()


def test_restricao_de_faixa_aumenta_a_correlacao_e_nao_muda_sem_restricao():
    assert est.corrigir_restricao_de_faixa(0.3, 0.08, 0.134) > 0.3
    assert est.corrigir_restricao_de_faixa(0.3, 0.1, 0.1) == pytest.approx(0.3)
