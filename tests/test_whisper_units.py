"""
Testes de unidade e validação temporal para scripts/whisper_to_remotion.py (NT-12).
"""

from pathlib import Path
import tempfile
import pytest

from scripts.whisper_to_remotion import (
    convert_whisper_tsv_to_remotion_props,
    parse_timestamp_to_seconds,
)


def test_parse_timestamp_units_ms():
    assert parse_timestamp_to_seconds("840", units="ms") == 0.84
    assert parse_timestamp_to_seconds("2500", units="ms") == 2.5


def test_parse_timestamp_units_s():
    assert parse_timestamp_to_seconds("0.84", units="s") == 0.84
    assert parse_timestamp_to_seconds("15.5", units="s") == 15.5


def test_parse_timestamp_units_auto():
    assert parse_timestamp_to_seconds("2500", units="auto") == 2.5
    assert parse_timestamp_to_seconds("2.5", units="auto") == 2.5


def test_convert_whisper_tsv_units_s():
    tsv_content = (
        "start\tend\ttext\n"
        "0.0\t1.5\tPrimeiro trecho em segundos\n"
        "1.5\t3.0\tSegundo trecho em segundos\n"
    )
    with tempfile.NamedTemporaryFile("w+", suffix=".tsv", delete=False, encoding="utf-8") as f:
        f.write(tsv_content)
        tsv_path = Path(f.name)

    try:
        props = convert_whisper_tsv_to_remotion_props(tsv_path, fps=60, units="s")
        assert props["fps"] == 60
        assert len(props["events"]) == 2
        assert props["events"][0]["startSeconds"] == 0.0
        assert props["events"][0]["endSeconds"] == 1.5
        assert props["events"][0]["startFrame"] == 0
        assert props["events"][0]["endFrame"] == 90
        assert props["events"][1]["startFrame"] == 90
        assert props["events"][1]["endFrame"] == 180
    finally:
        if tsv_path.exists():
            tsv_path.unlink()


def test_convert_whisper_tsv_temporal_validation_error():
    # Linha 2 tem end < start
    tsv_content = (
        "start\tend\ttext\n"
        "3000\t1000\tTexto com tempo invertido\n"
    )
    with tempfile.NamedTemporaryFile("w+", suffix=".tsv", delete=False, encoding="utf-8") as f:
        f.write(tsv_content)
        tsv_path = Path(f.name)

    try:
        with pytest.raises(ValueError) as excinfo:
            convert_whisper_tsv_to_remotion_props(tsv_path, fps=60, units="ms")
        err_msg = str(excinfo.value)
        assert "end" in err_msg and "start" in err_msg
        assert "Linha" in err_msg
    finally:
        if tsv_path.exists():
            tsv_path.unlink()
