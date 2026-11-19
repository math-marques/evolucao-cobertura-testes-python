import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PROJETOS = {
    "Flask": BASE_DIR / "resultados/flask/coverage_main.json",
    "Click": BASE_DIR / "resultados/click/coverage_main.json",
    "Requests": BASE_DIR / "resultados/requests/coverage_main.json",
}

def inspecionar_lacunas():
    for projeto, caminho_json in PROJETOS.items():
        if not caminho_json.exists():
            continue
        with open(caminho_json, encoding="utf-8") as f:
            data = json.load(f)

        print(f"\n{'='*65}\nAuditoria - {projeto.upper()}\n{'='*65}")
        candidatos = []
        for arq, info in data["files"].items():
            s = info["summary"]
            if s.get("num_branches", 0) >= 20 and s.get("missing_branches", 0) > 0:
                candidatos.append((
                    arq,
                    s["percent_statements_covered"],
                    s["percent_branches_covered"],
                    s["missing_branches"],
                    info.get("missing_branches", [])[:6], # Primeiros pares de ramos perdidos (linha_origem ---> linha_destino)
                    info.get("missing_lines", [])[:10]
                ))

        # ordenacao pelos modulos com maior quantidade de ramos achados
        candidatos.sort(key=lambda x: x[3], reverse=True)

        for arq, stmt, br, n_miss, pares_br, linhas_miss in candidatos[:4]:
            print(f"\nArquivo: {arq}")
            print(f"  - Stmt Coverage: {stmt:.1f}% | Branch Coverage: {br:.1f}% ({n_miss} ramos descobertos)")
            print(f"  - Exemplos de arestas (origem -> destino) não executadas: {pares_br}")
            print(f"  - Exemplos de linhas não executadas: {linhas_miss}")

if __name__ == "__main__":
    inspecionar_lacunas()