import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

PROJETOS = {
    "Flask": BASE_DIR / "resultados/flask",
    "Click": BASE_DIR / "resultados/click",
    "Requests": BASE_DIR / "resultados/requests",
}

def chave_versao(v):
    if "main" in v or "dev" in v:
        return (999, 999, 999, v)
    nums = [int(n) for n in re.findall(r"\d+", v)]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3]) + (v,)

def analisar_regressoes():
    for projeto, pasta in PROJETOS.items():
        arqs = sorted(pasta.glob("coverage_*.json"), key=lambda p: chave_versao(p.stem.replace("coverage_", "")))
        if len(arqs) < 2:
            continue

        print(f"\n{'='*65}\nEvolução diferencial por arquivo - {projeto.upper()}\n{'='*65}")
        for i in range(1, len(arqs)):
            v_ant = arqs[i-1].stem.replace("coverage_", "")
            v_atu = arqs[i].stem.replace("coverage_", "")

            d_ant = json.loads(arqs[i-1].read_text(encoding="utf-8"))["files"]
            d_atu = json.loads(arqs[i].read_text(encoding="utf-8"))["files"]

            regressoes = []
            melhorias = []
            for fp, info_atu in d_atu.items():
                if fp not in d_ant:
                    continue
                b_ant = d_ant[fp]["summary"].get("percent_branches_covered", 0.0)
                b_atu = info_atu["summary"].get("percent_branches_covered", 0.0)
                n_br = info_atu["summary"].get("num_branches", 0)
                if n_br > 0:
                    diff = round(b_atu - b_ant, 2)
                    if diff <= -0.5:
                        regressoes.append((Path(fp).name, b_ant, b_atu, diff, info_atu["summary"]["missing_branches"]))
                    elif diff >= 0.5:
                        melhorias.append((Path(fp).name, b_ant, b_atu, diff))

            if regressoes or melhorias:
                print(f"\nTransição: {v_ant} -> {v_atu}")
                for mod, ba, bt, df, miss in regressoes:
                    print(f"  [REGRESSÃO] {mod}: Branch {ba:.1f}% -> {bt:.1f}% ({df:+.2f}%) | {miss} ramos descobertos")
                for mod, ba, bt, df in melhorias:
                    print(f"  [MELHORIA]  {mod}: Branch {ba:.1f}% -> {bt:.1f}% ({df:+.2f}%)")

if __name__ == "__main__":
    analisar_regressoes()
