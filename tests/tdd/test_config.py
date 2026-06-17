# -*- coding: utf-8 -*-
"""
Testes unitários para WinFix v4.0.

Requisitos:
    pip install pytest pytest-asyncio

Executar se a pasta de binário não estiver no PATH:
    python -m pytest tests/tdd/test_config.py -v
"""

import pytest
import json
from unittest.mock import patch
import importlib

# Defina aqui qual arquivo você quer testar ("config_red", "config_green" ou config)
nome_arquivo = "config_green"
meu_modulo = importlib.import_module(nome_arquivo)


# =============================================================================
# TESTES: export_report
# =============================================================================

def test_load_config_arquivo_valido(tmp_path, monkeypatch):
    dados = {"version": "2.0", "last_run": "2025-01-01", "logs": []}
    arquivo = tmp_path / "winfix.json"
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
    monkeypatch.setattr(meu_modulo, "CONFIG_FILE", str(arquivo))
    resultado = meu_modulo.load_config()
    assert resultado["version"] == "2.0"

def test_load_config_arquivo_ausente(tmp_path, monkeypatch):
    monkeypatch.setattr(meu_modulo, "CONFIG_FILE", str(tmp_path / "nao_existe.json"))
    resultado = meu_modulo.load_config()
    assert "version" in resultado

def test_load_config_json_corrompido(tmp_path, monkeypatch):
    arquivo = tmp_path / "winfix.json"
    arquivo.write_text("{ isso nao é json válido !!!", encoding="utf-8")
    monkeypatch.setattr(meu_modulo, "CONFIG_FILE", str(arquivo))
    resultado = meu_modulo.load_config()
    assert "version" in resultado