"""Gera os extratos anonimizados em data/ a partir da pasta privada da operação de cortes.

Só sai o que a análise precisa: notas, critérios do juiz, plataforma, nicho, datas e métricas.
Não saem títulos, canais de origem, links, legendas, identificadores de conta nem nomes de pessoas.
O identificador de cada corte é um hash curto, sem volta para o vídeo original.

Uso:
    python scripts/extrair_dados.py "D:/apps/Cortes"
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

SAIDA = Path("data")
NICHOS = {"ciencia": "Ciência", "empreendedorismo": "Negócios", "gaming": "Games"}
CRITERIOS = ["hook_3s", "standalone", "complete_arc", "shareability", "emotion", "energy", "insight", "humour"]


def anonimo(fonte: str, corte: str) -> str:
    return hashlib.sha1(f"{fonte}_{corte}".encode()).hexdigest()[:10]


def ler(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def extrair_cortes(raiz: Path) -> tuple[list[dict], dict[tuple[str, str], str]]:
    linhas, chaves = [], {}
    for pasta in sorted((raiz / "runs" / "sources").glob("*/*")):
        if not (pasta / "scored.json").exists():
            continue
        pontuado = ler(pasta / "scored.json")
        nicho = pontuado.get("niche", pasta.parent.name)
        fonte = pontuado.get("source", pasta.name)
        juiz = {}
        if (pasta / "judge.json").exists():
            juiz = {linha["id"]: linha for linha in ler(pasta / "judge.json").get("scores", [])}
        for corte in pontuado.get("cuts", []):
            if corte.get("probability") is None:
                continue
            identificador = anonimo(fonte, corte["id"])
            chaves[(fonte, corte["id"])] = identificador
            notas_juiz = juiz.get(corte["id"], {})
            linha = {
                "corte": identificador,
                "nicho": NICHOS.get(nicho, nicho),
                "nota": round(float(corte["probability"]), 4),
                "nota_juiz": corte.get("p_judge"),
                "nota_metricas": corte.get("p_features"),
                "duracao_s": round(float(corte.get("end", 0)) - float(corte.get("start", 0)), 1),
            }
            for criterio in CRITERIOS:
                linha[criterio] = notas_juiz.get(criterio)
            linhas.append(linha)
    return linhas, chaves


def extrair_posts(raiz: Path, chaves: dict[tuple[str, str], str]) -> list[dict]:
    linhas = []
    for coleta in sorted((raiz / "runs" / "analytics").glob("20*.json")):
        coletado_em = datetime.fromtimestamp(coleta.stat().st_mtime).replace(microsecond=0)
        for post in ler(coleta):
            fonte, _, resto = post["external_id"].rpartition("_")
            corte_id, _, plataforma = resto.partition("-")
            identificador = chaves.get((fonte, corte_id))
            metricas = post.get("metrics") or {}
            if identificador is None or metricas.get("views") is None:
                continue
            publicado_em = datetime.fromisoformat(post["when"][:19])
            linhas.append(
                {
                    "coleta": coleta.stem,
                    "corte": identificador,
                    "nicho": NICHOS.get(post["niche"], post["niche"]),
                    "plataforma": plataforma or post.get("platform"),
                    "publicado_em": publicado_em.isoformat(),
                    "hora_publicacao": publicado_em.hour,
                    "horas_no_ar": round((coletado_em - publicado_em).total_seconds() / 3600, 1),
                    "views": int(metricas["views"]),
                    "curtidas": int(metricas.get("likes") or 0),
                    "comentarios": int(metricas.get("comments") or 0),
                    "taxa_ate_o_fim": metricas.get("full_video_watched_rate"),
                    "tempo_medio_s": metricas.get("average_time_watched"),
                }
            )
    return linhas


def extrair_agenda(raiz: Path) -> list[dict]:
    """Quantos posts estão agendados em cada semana, por plataforma (só os envios confirmados)."""
    from collections import Counter
    from datetime import date

    semanas: dict[str, Counter] = {}
    for entrega in ("leva-nov", "fase1-campanhas"):
        for registro in sorted((raiz / "entregas" / entrega).glob("*/upload_log.json")):
            enviados = {k for k, v in ler(registro).items() if v.get("ok")}
            with (registro.parent / "upload_queue.csv").open(encoding="utf-8", newline="") as arquivo:
                for linha in csv.DictReader(arquivo):
                    if linha["external_id"] not in enviados:
                        continue
                    dia = datetime.fromisoformat(linha["scheduled_date"][:19]).date()
                    segunda = date.fromordinal(dia.toordinal() - dia.weekday()).isoformat()
                    semanas.setdefault(segunda, Counter())[linha["platform"]] += 1
    return [
        {"semana": s, "tiktok": c.get("tiktok", 0), "youtube": c.get("youtube", 0)} for s, c in sorted(semanas.items())
    ]


def gravar(nome: str, linhas: list[dict]) -> None:
    SAIDA.mkdir(exist_ok=True)
    with (SAIDA / nome).open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    raiz = Path(sys.argv[1])
    cortes, chaves = extrair_cortes(raiz)
    posts = extrair_posts(raiz, chaves)
    gravar("cortes_pontuados.csv", cortes)
    gravar("posts_metricas.csv", posts)
    agenda = extrair_agenda(raiz)
    gravar("agenda_semanal.csv", agenda)
    print(f"agenda_semanal.csv: {len(agenda)} semanas, {sum(a['tiktok'] + a['youtube'] for a in agenda)} posts agendados")
    coletas = sorted({p["coleta"] for p in posts})
    print(f"cortes_pontuados.csv: {len(cortes)} cortes")
    print(f"posts_metricas.csv: {len(posts)} linhas em {len(coletas)} coletas ({coletas[0]} a {coletas[-1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
