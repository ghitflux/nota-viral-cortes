import numpy as np
import pandas as pd
import pytest

from nota_viral import analise, dados


def _cortes_e_posts(semente: int = 0):
    gerador = np.random.default_rng(semente)
    cortes = pd.DataFrame(
        {
            "corte": [f"c{i:03d}" for i in range(60)],
            "nicho": np.tile(["Ciência", "Negócios", "Games"], 20),
            "nota": gerador.uniform(0.2, 0.79, 60).round(3),
            "nota_juiz": gerador.uniform(0.1, 0.8, 60),
            "nota_metricas": gerador.uniform(0.3, 0.95, 60),
            "duracao_s": gerador.uniform(20, 60, 60),
            **{criterio: gerador.integers(1, 10, 60) for criterio in dados.CRITERIOS},
        }
    )
    linhas = []
    for coleta, extra in [("2026-11-09", 0), ("2026-11-10", 13)]:
        for i in range(30):
            for plataforma in ("tiktok", "youtube"):
                linhas.append(
                    {
                        "coleta": coleta,
                        "corte": f"c{i:03d}",
                        "nicho": cortes.loc[i, "nicho"],
                        "plataforma": plataforma,
                        "publicado_em": f"2026-11-0{7 + i % 3}T12:00:00",
                        "hora_publicacao": 12,
                        "horas_no_ar": 10.0 + 8 * (i % 6) + extra,
                        # Mesma base nas duas coletas: a segunda só acrescenta `extra` views.
                        "views": 100 + (37 * i) % 500 + (60 if plataforma == "tiktok" else 0) + extra,
                        "curtidas": 3,
                        "comentarios": 0,
                        "taxa_ate_o_fim": 0.05,
                        "tempo_medio_s": 8.0,
                    }
                )
    return cortes, pd.DataFrame(linhas)


def test_juntar_usa_a_coleta_mais_recente_e_cria_o_canal():
    cortes, posts = _cortes_e_posts()
    tabela = dados.juntar(cortes, posts)
    assert set(tabela["coleta"]) == {"2026-11-10"}
    assert len(tabela) == 60
    assert tabela["canal"].nunique() == 6
    assert "TikTok · Games" in set(tabela["canal"])
    assert tabela["nota"].notna().all()


def test_resumo_e_limiar():
    cortes, posts = _cortes_e_posts()
    tabela = dados.juntar(cortes, posts)
    resumo = analise.resumo_da_amostra(cortes, tabela, posts)
    assert resumo["cortes_pontuados"] == 60 and resumo["cortes_publicados"] == 30 and resumo["coletas"] == 2
    limiar = analise.limiar_de_aprovacao(cortes)
    assert limiar["cortes_no_limiar"] == 0 and limiar["nota_maxima"] < 0.80


def test_correlacoes_tem_as_quatro_comparacoes_com_intervalo_coerente():
    cortes, posts = _cortes_e_posts()
    tabela = dados.juntar(cortes, posts)
    resultado = analise.correlacoes(tabela, repeticoes=150)
    assert list(resultado.index) == [
        "Tudo junto (ingênua)",
        "Dentro de cada canal",
        "Dentro do canal, posts com mais de 24 h",
        "Dentro do canal, posts com menos de 24 h",
    ]
    assert (resultado["IC 95% inferior"] <= resultado["correlação"] + 0.25).all()
    assert (resultado["IC 95% superior"] >= resultado["correlação"] - 0.25).all()
    assert resultado["posts"].iloc[2] + resultado["posts"].iloc[3] == resultado["posts"].iloc[1]


def test_crescimento_entre_coletas_nunca_e_negativo_nos_dados_de_teste():
    _, posts = _cortes_e_posts()
    crescimento = analise.crescimento_entre_coletas(posts)
    assert crescimento.attrs["coletas"] == ("2026-11-09", "2026-11-10")
    assert (crescimento["ganho_mediano"] == 13).all()
    assert analise.crescimento_entre_coletas(posts[posts["coleta"] == "2026-11-10"]) is None


def test_plano_de_amostra_usa_a_agenda_acumulada():
    cortes, posts = _cortes_e_posts()
    tabela = dados.juntar(cortes, posts)
    agenda = pd.DataFrame({"semana": ["2026-11-02", "2026-11-09", "2026-11-16"], "tiktok": [20, 50, 60], "youtube": [20, 50, 60]})
    plano = analise.plano_de_amostra(tabela, agenda)
    assert plano.loc[0.5, "posts necessários"] == 30
    assert plano.loc[0.5, "semana em que a agenda chega lá"] == "2026-11-02"
    assert plano.loc[0.3, "semana em que a agenda chega lá"] == "2026-11-09"
    assert plano.loc[0.2, "semana em que a agenda chega lá"] == "2026-11-16"
    assert plano.attrs["detectavel_hoje"] == pytest.approx(0.356, abs=0.01)
