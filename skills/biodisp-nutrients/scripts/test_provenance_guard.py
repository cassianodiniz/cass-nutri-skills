#!/usr/bin/env python3
"""Pressure tests for the answer-provenance fail-closed gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


CASES = {
    "book_with_page_and_evidence": (
        "Origem: livro\n\nCozzolino (2012), PDF p. 278.\n"
        "Evidência [PDF p. 278]: RDA - ingestão dietética recomendada.\n",
        0,
    ),
    "book_without_page": ("Origem: livro\n\nSem página.\n", 1),
    "book_without_evidence": ("Origem: livro\n\nCozzolino (2012), PDF p. 278.\n", 1),
    "external_with_link": ("Origem: externa\n\nFonte externa: https://example.org/ref\n", 0),
    "unlabeled_model_memory": ("Segundo uma resposta anterior do Claude, seria este valor.\n", 1),
    "mixed_without_separation": (
        "Origem: livro\n\nCozzolino (2012), PDF p. 278.\n"
        "Evidência [PDF p. 278]: RDA - ingestão dietética recomendada.\n\n"
        "Origem: externa\n\nFonte externa: https://example.org/ref\n",
        1,
    ),
    "mixed_with_separation": (
        "Separação de fontes:\n\nOrigem: livro\n\nCozzolino (2012), PDF p. 278.\n"
        "Evidência [PDF p. 278]: RDA - ingestão dietética recomendada.\n\n"
        "Origem: externa\n\nFonte externa: https://example.org/ref\n",
        0,
    ),
    "invented_evidence": (
        "Origem: livro\n\nCozzolino (2012), PDF p. 278.\n"
        "Evidência [PDF p. 278]: este trecho não aparece na página do livro.\n",
        1,
    ),
    "nonexistent_book_page": (
        "Origem: livro\n\nCozzolino (2012), PDF p. 9999.\n"
        "Evidência [PDF p. 9999]: qualquer trecho inexistente.\n",
        1,
    ),
}


def main() -> int:
    checker = Path(__file__).with_name("check_answer_provenance.py")
    failures = []
    for name, (draft, expected) in CASES.items():
        result = subprocess.run(
            [sys.executable, str(checker), "-"],
            input=draft,
            text=True,
            capture_output=True,
            check=False,
        )
        actual = 0 if result.returncode == 0 else 1
        status = "PASS" if actual == expected else "FAIL"
        print(f"{status}: {name} expected={expected} actual={actual}")
        if status == "FAIL":
            failures.append(name)
    print(f"{len(CASES) - len(failures)}/{len(CASES)} provenance pressure tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
