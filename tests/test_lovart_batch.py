import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import lovart_batch  # noqa: E402


def test_read_prompts_txt(tmp_path):
    f = tmp_path / "prompts.txt"
    f.write_text("a logo\n\n  a poster  \n", encoding="utf-8")
    assert lovart_batch.read_prompts(f) == ["a logo", "a poster"]


def test_read_prompts_csv(tmp_path):
    f = tmp_path / "prompts.csv"
    f.write_text("prompt,style\na logo,flat\na poster,bold\n", encoding="utf-8")
    assert lovart_batch.read_prompts(f) == ["a logo", "a poster"]


def test_read_prompts_csv_missing_column(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("name,style\nx,flat\n", encoding="utf-8")
    with pytest.raises(ValueError):
        lovart_batch.read_prompts(f)
