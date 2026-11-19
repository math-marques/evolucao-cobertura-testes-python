import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EXPERIMENTOS = {
    "flask": {
        "repo_dir": BASE_DIR / "repos/flask",
        "out_dir": BASE_DIR / "resultados/flask",
        "source_pkg": "src/flask",
        "tags": [
            "2.2.x", "2.3.x", "2.3.3",
            "3.0.0", "3.0.1", "3.0.2", "3.0.3",
            "3.1.0", "3.1.1", "3.1.2", "3.1.3", "main"
        ]
    },
    "click": {
        "repo_dir": BASE_DIR / "repos/click",
        "out_dir": BASE_DIR / "resultados/click",
        "source_pkg": "src/click",
        "tags": [
            "8.1.4", "8.1.5", "8.1.6", "8.1.7", "8.1.8",
            "8.2.0", "8.2.1", "8.2.2",
            "8.3.0", "8.3.1", "8.3.2", "8.3.3",
            "8.4.0", "8.4.1", "8.4.2", "8.5.0", "main"
        ]
    },
    "requests": {
        "repo_dir": BASE_DIR / "repos/requests",
        "out_dir": BASE_DIR / "resultados/requests",
        "source_pkg": "src/requests",
        "tags": [
            "v2.32.0", "v2.32.1", "v2.32.2", "v2.32.3", "v2.32.4", "v2.32.5",
            "v2.33.0", "v2.33.1",
            "v2.34.0", "v2.34.1", "v2.34.2", "main"
        ]
    }
}

def rodar(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return res.returncode == 0, res.stderr

def coletar(projeto, cfg):
    repo_dir = cfg["repo_dir"]
    out_dir = cfg["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    venv_dir = repo_dir / ".venv_exp"

    print(f"\n=== COLETANDO: {projeto.upper()} ===")
    for tag in cfg["tags"]:
        tag_limpa = tag.lstrip("v")
        json_destino = out_dir / f"coverage_{tag_limpa}.json"

        if json_destino.exists():
            print(f"[PULANDO] {projeto} {tag}")
            continue

        rodar(["git", "reset", "--hard"], repo_dir)
        rodar(["git", "clean", "-fd", "-e", ".venv_exp"], repo_dir)
        ok_git, err_git = rodar(["git", "checkout", tag], repo_dir)
        if not ok_git:
            print(f"[ERRO GIT] {tag}: {err_git.strip()}")
            continue

        if venv_dir.exists():
            shutil.rmtree(venv_dir, ignore_errors=True)
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

        py_bin = str(venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))

        rodar([py_bin, "-m", "pip", "install", "--upgrade", "pip", "pytest", "coverage"], repo_dir)
        if (repo_dir / "requirements/tests.txt").exists():
            rodar([py_bin, "-m", "pip", "install", "-r", "requirements/tests.txt"], repo_dir)
        elif (repo_dir / "requirements-dev.txt").exists():
            rodar([py_bin, "-m", "pip", "install", "-r", "requirements-dev.txt"], repo_dir)
        rodar([py_bin, "-m", "pip", "install", "-e", "."], repo_dir)

        pkg_path = cfg["source_pkg"] if (repo_dir / cfg["source_pkg"]).exists() else projeto
        rodar([py_bin, "-m", "coverage", "run", "--branch", f"--source={pkg_path}", "-m", "pytest", "-q"], repo_dir)

        if (repo_dir / ".coverage").exists():
            ok_json, _ = rodar([py_bin, "-m", "coverage", "json", "-o", str(json_destino)], repo_dir)
            if ok_json:
                with open(json_destino, encoding="utf-8") as f:
                    cov = json.load(f)["totals"]["percent_statements_covered"]
                if cov < 45.0:
                    print(f"[DESCARTADO] {tag} ({cov:.1f}% - falha de importação)")
                    json_destino.unlink()
                else:
                    print(f"[OK] {tag} -> {cov:.1f}% statements")

if __name__ == "__main__":
    for nome, config in EXPERIMENTOS.items():
        if config["repo_dir"].exists():
            coletar(nome, config)
        else:
            print(f"[AVISO] Pasta {config['repo_dir']} não encontrada.")
