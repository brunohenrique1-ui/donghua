#!/usr/bin/env python3
"""Validate the structure and Markdown files of a GitHub project repository."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXPECTED_FILES = {
    "README.md",
    "docs/overview.md",
    "worldbuilding/universe.md",
    "worldbuilding/territory.md",
    "characters/protagonist.md",
    "episodes/episode-01-script.md",
    "episodes/episode-01-breakdown.md",
    "episodes/episode-01-shot-list.md",
    "episodes/episode-01-storyboard.md",
    "prompts/image.md",
    "prompts/video.md",
    "prompts/sound.md",
}

REQUIRED_HEADINGS = {
    "README.md": ["# "],
    "episodes/episode-01-script.md": ["# ", "## ", "Cena"],
    "episodes/episode-01-breakdown.md": ["# ", "Cena"],
}


def markdown_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if ".git" not in p.parts)


def normalized(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix().lower()


def validate(root: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    root = root.resolve()

    if not root.is_dir():
        print(f"ERRO: diretório não encontrado: {root}")
        return 2

    files = markdown_files(root)
    relative = {normalized(p, root): p for p in files}

    if "readme.md" not in relative:
        errors.append("README.md não encontrado na raiz do repositório.")

    for expected in sorted(EXPECTED_FILES):
        key = expected.lower()
        if key not in relative:
            warnings.append(f"Arquivo recomendado ausente: {expected}")

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        if not text.strip():
            errors.append(f"Arquivo Markdown vazio: {rel}")
        if "Enter file contents here" in text:
            errors.append(f"Arquivo contém texto-placeholder do GitHub: {rel}")
        if re.search(r"\s+$", text, flags=re.MULTILINE):
            warnings.append(f"Linhas com espaços finais: {rel}")

    for expected, headings in REQUIRED_HEADINGS.items():
        path = relative.get(expected.lower())
        if not path:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for heading in headings:
            if heading not in text:
                errors.append(f"{expected} não contém o padrão esperado: {heading!r}")

    # Detect likely accidental nesting such as prompts/prompts or repeated folders.
    for path in files:
        parts = [p.lower() for p in path.relative_to(root).parts[:-1]]
        for left, right in zip(parts, parts[1:]):
            if left == right:
                warnings.append(
                    f"Pastas repetidas no caminho: {path.relative_to(root).as_posix()}"
                )
                break

    print(f"Arquivos Markdown encontrados: {len(files)}")
    for warning in sorted(set(warnings)):
        print(f"AVISO: {warning}")
    for error in sorted(set(errors)):
        print(f"ERRO: {error}")

    if errors:
        print(f"\nValidação falhou: {len(set(errors))} erro(s).")
        return 1
    print("\nValidação concluída sem erros bloqueadores.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Diretório do repositório")
    args = parser.parse_args()
    return validate(Path(args.repo))


if __name__ == "__main__":
    sys.exit(main())
