import csv
import glob
import json
import os
import re
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent

PROJETOS = {
    "Flask": BASE_DIR / "resultados/flask",
    "Click": BASE_DIR / "resultados/click",
    "Requests": BASE_DIR / "resultados/requests",
}

SAIDA_DIR = BASE_DIR / "relatorio_final"

def chave_versao(v):
    if "main" in v or "dev" in v:
        return (999, 999, 999, v)
    nums = [int(n) for n in re.findall(r"\d+", v)]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3]) + (v,)

def carregar_dados(pasta):
    resultados = []
    for arq in glob.glob(str(pasta / "coverage_*.json")):
        versao = os.path.basename(arq).replace("coverage_", "").replace(".json", "")
        with open(arq, encoding="utf-8") as f:
            data = json.load(f)

        totals = data["totals"]
        modulos = [
            (os.path.basename(fp), info["summary"]["percent_branches_covered"], info["summary"]["missing_branches"])
            for fp, info in data["files"].items()
            if info["summary"].get("num_branches", 0) > 0
        ]
        modulos.sort(key=lambda x: x[1])

        resultados.append({
            "versao": versao,
            "statements_pct": round(totals["percent_statements_covered"], 2),
            "branches_pct": round(totals.get("percent_branches_covered", 0.0), 2),
            "total_statements": totals["num_statements"],
            "total_branches": totals.get("num_branches", 0),
            "covered_branches": totals.get("covered_branches", 0),
            "missing_branches": totals.get("missing_branches", 0),
            "piores_modulos": modulos[:3],
        })

    resultados.sort(key=lambda x: chave_versao(x["versao"]))
    return resultados

def gerar_grafico(projeto, dados):
    if len(dados) < 2:
        return
    versoes = [d["versao"] for d in dados]
    stmt = [d["statements_pct"] for d in dados]
    branch = [d["branches_pct"] for d in dados]
    ramos = [d["total_branches"] for d in dados]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    ax1.plot(versoes, stmt, marker="o", linewidth=2, label="Statement Coverage (%)", color="#1f77b4")
    ax1.plot(versoes, branch, marker="s", linewidth=2, label="Branch Coverage (%)", color="#d62728")
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("Cobertura (%)")
    ax1.set_title(f"Evolução da Cobertura Estrutural - {projeto}")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend()

    ax2.bar(versoes, ramos, color="#2ca02c", alpha=0.75, label="Total de Branches (Ramos)")
    ax2.set_ylabel("Qtd. de Ramos")
    ax2.set_xlabel("Versão (Release)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend()

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(SAIDA_DIR / f"grafico_evolucao_{projeto.lower()}.png", dpi=300)
    plt.close()

def gerar_markdown(projeto, dados):
    linhas = [f"# Análise de Evolução - {projeto}\n*Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n\n"]
    for i, atual in enumerate(dados):
        piores = ", ".join([f"`{m[0]}` ({m[1]:.1f}%)" for m in atual["piores_modulos"]])
        linhas.append(f"## `{atual['versao']}`\n")
        linhas.append(f"- **Statement:** {atual['statements_pct']}% | **Branch:** {atual['branches_pct']}% ({atual['covered_branches']}/{atual['total_branches']})\n")
        linhas.append(f"- **Módulos críticos (menor branch coverage):** {piores}\n")
        if i > 0:
            ant = dados[i - 1]
            linhas.append(f"- **Delta vs `{ant['versao']}`:** Stmt `{atual['statements_pct'] - ant['statements_pct']:+.2f}%` | Branch `{atual['branches_pct'] - ant['branches_pct']:+.2f}%` | Ramos `{atual['total_branches'] - ant['total_branches']:+d}`\n")
        linhas.append("\n")
    with open(SAIDA_DIR / f"analise_{projeto.lower()}.md", "w", encoding="utf-8") as f:
        f.writelines(linhas)

def executar():
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    comparativo = []

    for projeto, pasta in PROJETOS.items():
        dados = carregar_dados(pasta)
        if not dados:
            continue

        campos = ["versao", "statements_pct", "branches_pct", "total_statements", "total_branches", "covered_branches", "missing_branches"]
        with open(SAIDA_DIR / f"metricas_{projeto.lower()}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            w.writeheader()
            w.writerows(dados)

        gerar_grafico(projeto, dados)
        gerar_markdown(projeto, dados)

        ini, fim = dados[0], dados[-1]
        comparativo.append({
            "projeto": projeto,
            "versoes_validas": len(dados),
            "faixa": f"{ini['versao']} -> {fim['versao']}",
            "statement_ini_fim": f"{ini['statements_pct']}% -> {fim['statements_pct']}%",
            "branch_ini_fim": f"{ini['branches_pct']}% -> {fim['branches_pct']}%",
            "delta_ramos": fim["total_branches"] - ini["total_branches"],
            "gap_stmt_branch_atual": round(fim["statements_pct"] - fim["branches_pct"], 2),
        })

    if comparativo:
        with open(SAIDA_DIR / "comparativo_geral_projetos.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=comparativo[0].keys())
            w.writeheader()
            w.writerows(comparativo)
        print("[SUCESSO] Todos os relatórios e gráficos foram gerados em relatorio_final/")

if __name__ == "__main__":
    executar()
