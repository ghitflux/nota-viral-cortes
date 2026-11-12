"""Gráficos adicionais para o site, como dados, para ele desenhar nativamente (`para_o_site.graficos_extras`).

O texto e o gráfico principal deste estudo (nota x views) vêm de outro arquivo do site; aqui saem só os extras,
cada um equivalente a uma figura ou tabela do README. Todo valor sai do dicionário de resultados gravado por
`scripts/rodar_analise.py`; nada é digitado à mão. Os canais aparecem só como plataforma e nicho.
"""

from __future__ import annotations

IDIOMAS = ("pt", "en", "es")
INGENUA = "Tudo junto (ingênua)"
DENTRO = "Dentro de cada canal"
ESTAVEIS = "Dentro do canal, posts com mais de 24 h"
COMPARACOES = {
    INGENUA: ("Tudo junto (ingênua)", "All together (naive)", "Todo junto (ingenua)"),
    DENTRO: ("Dentro de cada canal", "Within each channel", "Dentro de cada canal"),
    ESTAVEIS: ("Dentro do canal, mais de 24 h no ar", "Within channel, over 24 h live", "Dentro del canal, más de 24 h"),
    "Dentro do canal, posts com menos de 24 h": (
        "Dentro do canal, menos de 24 h no ar",
        "Within channel, under 24 h live",
        "Dentro del canal, menos de 24 h",
    ),
}
NICHOS = {"Games": ("Games", "Gaming", "Videojuegos"), "Negócios": ("Negócios", "Business", "Negocios"), "Ciência": ("Ciência", "Science", "Ciencia")}
PLATAFORMAS = {"tiktok": "TikTok", "youtube": "YouTube"}
IDADES = {
    "menos de 24 h": ("menos de 24 h", "under 24 h", "menos de 24 h"),
    "24 a 48 h": ("24 a 48 h", "24 to 48 h", "24 a 48 h"),
    "mais de 48 h": ("mais de 48 h", "over 48 h", "más de 48 h"),
}
COMPONENTES = {
    "ensina algo": ("ensina algo", "teaches something", "enseña algo"),
    "gancho nos 3 primeiros segundos": ("gancho nos 3 primeiros segundos", "hook in the first 3 seconds", "gancho en los 3 primeros segundos"),
    "humor": ("humor", "humor", "humor"),
    "dá vontade de compartilhar": ("dá vontade de compartilhar", "makes you want to share", "dan ganas de compartir"),
    "nota do juiz de IA": ("nota do juiz de IA", "AI judge score", "nota del juez de IA"),
    "nota das métricas do vídeo de origem": ("métricas do vídeo de origem", "source-video metrics", "métricas del video de origen"),
    "começo, meio e fim": ("começo, meio e fim", "beginning, middle and end", "principio, medio y fin"),
    "energia": ("energia", "energy", "energía"),
    "faz sentido sozinho": ("faz sentido sozinho", "stands on its own", "se entiende solo"),
    "emoção": ("emoção", "emotion", "emoción"),
}
MARCOS = {
    "fim de novembro": ("no fim de novembro", "by the end of November", "a fines de noviembre"),
    "fim de dezembro": ("no fim de dezembro", "by the end of December", "a fines de diciembre"),
    "fim da agenda": ("no fim da agenda", "by the end of the schedule", "al final de la agenda"),
}


def _n(valor: float, casas: int) -> dict[str, str]:
    """O mesmo número nos três idiomas (pt e es com vírgula decimal; sinal de menos tipográfico)."""
    texto = f"{valor:.{casas}f}".replace("-", "−")
    return {"pt": texto.replace(".", ","), "en": texto, "es": texto.replace(".", ",")}


def _milhar(valor: float) -> dict[str, str]:
    us = f"{valor:,.0f}"
    return {"pt": us.replace(",", "."), "en": us, "es": us.replace(",", ".")}


def _traduzir(tabela: dict[str, tuple[str, str, str]], chave: str) -> dict[str, str]:
    return dict(zip(IDIOMAS, tabela.get(chave, (chave, chave, chave))))


def _canal(nome: str) -> dict[str, str]:
    """'TikTok · Games' nos três idiomas (só o nicho muda)."""
    plataforma, _, nicho = nome.partition(" · ")
    return {i: f"{plataforma} · {t}" for i, t in _traduzir(NICHOS, nicho).items()}


def _rotulos(nomes: list[dict[str, str]]) -> dict[str, list[str]]:
    return {i: [n[i] for n in nomes] for i in IDIOMAS}


def correlacoes(r: dict) -> dict:
    """Barras: a correlação nota x views em cada comparação, da ingênua à mais justa."""
    c = r["correlacoes"]
    ordem = list(c)
    rotulos = _rotulos([_traduzir(COMPARACOES, k) for k in ordem])
    a, b, d = (_n(c[k]["correlação"], 2) for k in (INGENUA, DENTRO, ESTAVEIS))
    inf, sup, n = _n(c[ESTAVEIS]["IC 95% inferior"], 2), _n(c[ESTAVEIS]["IC 95% superior"], 2), c[ESTAVEIS]["posts"]
    return {
        "tipo": "barras",
        "titulo": {
            "pt": f"A resposta muda conforme a comparação fica mais justa: {a['pt']} → {b['pt']} → {d['pt']}",
            "en": f"The answer shifts as the comparison gets fairer: {a['en']} → {b['en']} → {d['en']}",
            "es": f"La respuesta cambia a medida que la comparación es más justa: {a['es']} → {b['es']} → {d['es']}",
        },
        "leitura": {
            "pt": f"Correlação de postos entre nota e views. Entre os {n} posts com views já estabilizadas, o intervalo de 95% vai de {inf['pt']} a {sup['pt']}: o sinal vinha dos posts mais novos, e a amostra ainda não permite separar a nota do lote do dia.",
            "en": f"Rank correlation between score and views. Among the {n} posts whose views have settled, the 95% interval runs from {inf['en']} to {sup['en']}: the signal came from the newest posts, and the sample cannot yet separate the score from the day's batch.",
            "es": f"Correlación de rangos entre nota y vistas. Entre los {n} posts con vistas ya estabilizadas, el intervalo del 95% va de {inf['es']} a {sup['es']}: la señal venía de los posts más nuevos, y la muestra aún no permite separar la nota del lote del día.",
        },
        "eixo_x": {"pt": "Comparação", "en": "Comparison", "es": "Comparación"},
        "eixo_y": {"pt": "Correlação de Spearman", "en": "Spearman correlation", "es": "Correlación de Spearman"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": [
            {
                "nome": {"pt": "Correlação nota x views", "en": "Score vs views correlation", "es": "Correlación nota x vistas"},
                "papel": "principal",
                "pontos": [[rotulos["pt"][k], round(c[nome]["correlação"], 4)] for k, nome in enumerate(ordem)],
                "rotulos": rotulos,
            }
        ],
    }


def views_por_canal(r: dict) -> dict:
    """Barras: mediana de views por canal (plataforma e nicho)."""
    canais = r["views_por_canal"]
    ordem = list(canais)
    rotulos = _rotulos([_canal(k) for k in ordem])
    medianas = [canais[k]["views_mediana"] for k in ordem]
    menor, maior = _milhar(min(medianas)), _milhar(max(medianas))
    return {
        "tipo": "barras",
        "titulo": {
            "pt": f"O canal pesa mais que a nota: mediana de {menor['pt']} a {maior['pt']} views conforme o canal",
            "en": f"The channel matters more than the score: median of {menor['en']} to {maior['en']} views by channel",
            "es": f"El canal pesa más que la nota: mediana de {menor['es']} a {maior['es']} vistas según el canal",
        },
        "leitura": {
            "pt": "Mediana de views dos posts de cada canal. Cada canal joga numa faixa própria, e o nicho de games recebe as notas mais altas e é o único com audiência no YouTube; por isso a comparação justa é dentro do canal.",
            "en": "Median views of each channel's posts. Each channel plays in its own range, and the gaming niche gets the highest scores and is the only one with a YouTube audience, so the fair comparison is within the channel.",
            "es": "Mediana de vistas de los posts de cada canal. Cada canal juega en su propio rango, y el nicho de videojuegos recibe las notas más altas y es el único con audiencia en YouTube; por eso la comparación justa es dentro del canal.",
        },
        "eixo_x": {"pt": "Canal", "en": "Channel", "es": "Canal"},
        "eixo_y": {"pt": "Mediana de views", "en": "Median views", "es": "Mediana de vistas"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": [
            {
                "nome": {"pt": "Mediana de views", "en": "Median views", "es": "Mediana de vistas"},
                "papel": "principal",
                "pontos": [[rotulos["pt"][k], round(v, 1)] for k, v in enumerate(medianas)],
                "rotulos": rotulos,
            }
        ],
    }


def poder(r: dict) -> dict:
    """Linhas: a menor correlação detectável (80% de poder) conforme o número de posts."""
    plano = r["plano_de_amostra"]
    hoje = _n(plano["detectavel_hoje"], 2)
    alvo = min(plano["tabela"], key=float)
    necessarios = _milhar(plano["tabela"][alvo]["posts necessários"])
    alvo_txt = _n(float(alvo), 1)
    marcos = [m for m in r["marcos_da_agenda"] if m["marco"] in MARCOS]
    partes = {i: ", ".join(f"{_milhar(m['posts'])[i]} posts {_traduzir(MARCOS, m['marco'])[i]}" for m in marcos) for i in IDIOMAS}
    return {
        "tipo": "linhas",
        "titulo": {
            "pt": f"Hoje a amostra só detecta correlação de {hoje['pt']} ou mais; {alvo_txt['pt']} pede {necessarios['pt']} posts",
            "en": f"Today the sample only detects correlations of {hoje['en']} or more; {alvo_txt['en']} needs {necessarios['en']} posts",
            "es": f"Hoy la muestra solo detecta correlaciones de {hoje['es']} o más; {alvo_txt['es']} pide {necessarios['es']} posts",
        },
        "leitura": {
            "pt": f"Menor correlação que a amostra detecta com 80% de poder, por número de posts. A agenda já programada soma {partes['pt']}, e as métricas são coletadas todo dia.",
            "en": f"Smallest correlation the sample detects with 80% power, by number of posts. The publishing schedule already adds up to {partes['en']}, and metrics are collected daily.",
            "es": f"Menor correlación que la muestra detecta con 80% de potencia, por número de posts. La agenda ya programada suma {partes['es']}, y las métricas se recogen todos los días.",
        },
        "eixo_x": {"pt": "Posts com métricas", "en": "Posts with metrics", "es": "Posts con métricas"},
        "eixo_y": {"pt": "Correlação detectável", "en": "Detectable correlation", "es": "Correlación detectable"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": [
            {
                "nome": {"pt": "Correlação detectável (80% de poder)", "en": "Detectable correlation (80% power)", "es": "Correlación detectable (80% de potencia)"},
                "papel": "principal",
                "pontos": [[int(p["posts"]), round(p["correlação detectável"], 4)] for p in r["curva_de_poder"]][:80],
            }
        ],
    }


def views_por_idade(r: dict) -> dict:
    """Barras: mediana de views por tempo no ar, uma série por plataforma."""
    linhas = r["views_por_idade"]
    idades = list(dict.fromkeys(l["horas_no_ar"] for l in linhas))
    rotulos = _rotulos([_traduzir(IDADES, k) for k in idades])
    plataformas = list(dict.fromkeys(l["plataforma"] for l in linhas))
    valor = {(l["plataforma"], l["horas_no_ar"]): l["views_mediana"] for l in linhas}
    yt_novo, yt_velho = _milhar(valor[("youtube", idades[0])]), _milhar(valor[("youtube", idades[-1])])
    papeis = {"tiktok": "alternativa", "youtube": "principal"}
    return {
        "tipo": "barras",
        "titulo": {
            "pt": f"As views chegam no primeiro dia: no YouTube, {yt_novo['pt']} de mediana no lote novo contra {yt_velho['pt']}",
            "en": f"Views arrive on day one: on YouTube, a median of {yt_novo['en']} in the new batch vs {yt_velho['en']}",
            "es": f"Las vistas llegan el primer día: en YouTube, mediana de {yt_novo['es']} en el lote nuevo frente a {yt_velho['es']}",
        },
        "leitura": {
            "pt": "Mediana de views por tempo no ar. Depois de 24 horas o número quase não sobe; o lote mais recente do YouTube foi melhor que os anteriores, e é esse lote que inflava a correlação.",
            "en": "Median views by time live. After 24 hours the count barely moves; YouTube's most recent batch did better than earlier ones, and that batch is what inflated the correlation.",
            "es": "Mediana de vistas por tiempo publicado. Después de 24 horas el número casi no sube; el lote más reciente de YouTube rindió más que los anteriores, y es ese lote el que inflaba la correlación.",
        },
        "eixo_x": {"pt": "Tempo no ar", "en": "Time live", "es": "Tiempo publicado"},
        "eixo_y": {"pt": "Mediana de views", "en": "Median views", "es": "Mediana de vistas"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": [
            {
                "nome": {i: PLATAFORMAS.get(p, p) for i in IDIOMAS},
                "papel": papeis.get(p, "neutro"),
                "pontos": [[rotulos["pt"][k], round(valor[(p, idade)], 1)] for k, idade in enumerate(idades)],
                "rotulos": rotulos,
            }
            for p in plataformas
        ],
    }


def componentes(r: dict) -> dict:
    """Barras: correlação dentro do canal de cada componente da nota."""
    comp = r["componentes_da_nota"]
    ordem = list(comp)
    rotulos = _rotulos([_traduzir(COMPONENTES, k) for k in ordem])
    menor_p = min(c["p ajustado"] for c in comp.values())
    p = _n(menor_p, 2)
    if menor_p >= 0.05:
        titulo = {
            "pt": f"Nenhuma parte da nota resiste à correção para múltiplos testes (p ajustado ≥ {p['pt']})",
            "en": f"No part of the score survives the multiple-testing correction (adjusted p ≥ {p['en']})",
            "es": f"Ninguna parte de la nota resiste la corrección por pruebas múltiples (p ajustado ≥ {p['es']})",
        }
    else:
        quantos = sum(c["p ajustado"] < 0.05 for c in comp.values())
        titulo = {
            "pt": f"{quantos} de {len(comp)} partes da nota resistem à correção para múltiplos testes",
            "en": f"{quantos} of {len(comp)} parts of the score survive the multiple-testing correction",
            "es": f"{quantos} de {len(comp)} partes de la nota resisten la corrección por pruebas múltiples",
        }
    return {
        "tipo": "barras",
        "titulo": titulo,
        "leitura": {
            "pt": f"Correlação dentro do canal entre cada um dos {len(comp)} componentes da nota e as views, com p-valor ajustado por Benjamini-Hochberg. Nenhum componente se destaca o bastante para guiar a recalibração.",
            "en": f"Within-channel correlation between each of the {len(comp)} score components and views, with Benjamini-Hochberg adjusted p-values. No component stands out enough to guide a recalibration.",
            "es": f"Correlación dentro del canal entre cada uno de los {len(comp)} componentes de la nota y las vistas, con p-valor ajustado por Benjamini-Hochberg. Ningún componente destaca lo suficiente para guiar la recalibración.",
        }
        if menor_p >= 0.05
        else {
            "pt": f"Correlação dentro do canal entre cada um dos {len(comp)} componentes da nota e as views, com p-valor ajustado por Benjamini-Hochberg.",
            "en": f"Within-channel correlation between each of the {len(comp)} score components and views, with Benjamini-Hochberg adjusted p-values.",
            "es": f"Correlación dentro del canal entre cada uno de los {len(comp)} componentes de la nota y las vistas, con p-valor ajustado por Benjamini-Hochberg.",
        },
        "eixo_x": {"pt": "Componente da nota", "en": "Score component", "es": "Componente de la nota"},
        "eixo_y": {"pt": "Correlação dentro do canal", "en": "Within-channel correlation", "es": "Correlación dentro del canal"},
        "formato_x": "numero",
        "formato_y": "numero",
        "series": [
            {
                "nome": {"pt": "Correlação dentro do canal", "en": "Within-channel correlation", "es": "Correlación dentro del canal"},
                "papel": "principal",
                "pontos": [[rotulos["pt"][k], round(comp[c]["correlação dentro do canal"], 4)] for k, c in enumerate(ordem)],
                "rotulos": rotulos,
            }
        ],
    }


def graficos_extras(r: dict) -> list[dict]:
    """As cinco especificações, do achado mais importante para o menos."""
    return [correlacoes(r), views_por_canal(r), poder(r), views_por_idade(r), componentes(r)]
