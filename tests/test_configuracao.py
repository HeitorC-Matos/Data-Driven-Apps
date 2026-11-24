import pytest

import config


def test_validar_gemini_sem_chave(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Chave"):
        config.verificar_configuracao()


def test_validar_gemini_com_chave(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "chave-exemplo")
    monkeypatch.setattr(config, "MODELO", "gemini-3.8-flash")
    config.verificar_configuracao()


def test_validar_modelo_vazio(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "chave-exemplo")
    monkeypatch.setattr(config, "MODELO", "")
    with pytest.raises(ValueError, match="GEMINI_MODEL"):
        config.verificar_configuracao()
