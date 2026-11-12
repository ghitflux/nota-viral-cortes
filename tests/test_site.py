"""Os gráficos extras do site: forma, limites, três idiomas e valores vindos dos resultados gravados."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from nota_viral import site

RESULTADOS = Path(__file__).resolve().parents[1] / "reports" / "resultados.json"
IDIOMAS = {"pt", "en", "es"}
PAPEIS = {"principal", "base", "alternativa", "neutro"}
FORMATOS = {"numero", "percentual", "data"}


@pytest.fixture(scope="module")
def resultados() -> dict:
    if not RESULTADOS.exists():
        pytest.skip("reports/resultados.json ainda não foi gerado")
    return json.loads(RESULTADOS.read_text(encoding="utf-8"))


def test_graficos_extras_tem_a_forma_que_o_site_espera(resultados):
    extras = site.graficos_extras(resultados)
    assert 3 <= len(extras) <= 5
    for g in extras:
        assert g["tipo"] in {"linhas", "barras", "pontos"}
        for campo in ("titulo", "leitura", "eixo_x", "eixo_y"):
            assert set(g[campo]) == IDIOMAS
            assert all(isinstance(v, str) and v.strip() for v in g[campo].values())
        assert all(len(t) <= 90 for t in g["titulo"].values()), g["titulo"]
        assert g["formato_x"] in FORMATOS and g["formato_y"] in FORMATOS
        assert 1 <= len(g["series"]) <= 4
        for serie in g["series"]:
            assert set(serie["nome"]) == IDIOMAS
            assert serie["papel"] in PAPEIS
            limite = 300 if g["tipo"] == "pontos" else 80
            assert 1 <= len(serie["pontos"]) <= limite
            for x, y in serie["pontos"]:
                assert isinstance(y, (int, float)) and math.isfinite(y)
                assert isinstance(x, str) if g["tipo"] == "barras" else isinstance(x, (int, float))
            if g["tipo"] == "barras":
                assert set(serie["rotulos"]) == IDIOMAS
                assert all(len(v) == len(serie["pontos"]) for v in serie["rotulos"].values())
                assert [p[0] for p in serie["pontos"]] == serie["rotulos"]["pt"]
        assert "faixa" not in g or g["tipo"] == "linhas"


def test_o_json_gravado_traz_os_extras_e_so_eles_no_bloco_do_site(resultados):
    assert set(resultados["para_o_site"]) == {"graficos_extras"}
    sem_bloco = {k: v for k, v in resultados.items() if k != "para_o_site"}
    assert resultados["para_o_site"]["graficos_extras"] == site.graficos_extras(sem_bloco)


def test_os_valores_dos_extras_saem_dos_resultados(resultados):
    correlacoes, canais, poder, idade, componentes = site.graficos_extras(resultados)
    ingenua = resultados["correlacoes"][site.INGENUA]["correlação"]
    assert f"{ingenua:.2f}".replace(".", ",") in correlacoes["titulo"]["pt"]
    assert f"{ingenua:.2f}" in correlacoes["titulo"]["en"]
    assert len(canais["series"][0]["pontos"]) == len(resultados["views_por_canal"])
    assert poder["series"][0]["pontos"][0][0] == resultados["curva_de_poder"][0]["posts"]
    assert {s["nome"]["pt"] for s in idade["series"]} == {"TikTok", "YouTube"}
    assert len(componentes["series"][0]["pontos"]) == len(resultados["componentes_da_nota"])

    alterado = copy.deepcopy(resultados)
    alterado["componentes_da_nota"]["humor"]["p ajustado"] = 0.01
    assert site.componentes(alterado)["titulo"]["pt"].startswith("1 de 10")


def test_traducoes_dos_rotulos():
    assert site._canal("YouTube · Negócios") == {"pt": "YouTube · Negócios", "en": "YouTube · Business", "es": "YouTube · Negocios"}
    assert site._traduzir(site.IDADES, "mais de 48 h")["es"] == "más de 48 h"
    assert site._traduzir({}, "outro") == {"pt": "outro", "en": "outro", "es": "outro"}
    assert site._n(-0.2999, 2) == {"pt": "−0,30", "en": "−0.30", "es": "−0,30"}
