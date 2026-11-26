# Pruebas del servidor local unificado (frontend + API).
from fastapi.testclient import TestClient

import config
import main


def _cliente(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_DB_PATH, str(tmp_path / "catdic_test.db"))
    monkeypatch.setenv(config.ENV_DROPBOX_RAIZ, str(tmp_path / "dropbox"))
    return TestClient(main.app)


def test_clasico_entrega_el_tablero_anterior(tmp_path, monkeypatch):
    """El tablero anterior (Control Taller) sigue en /clasico/ hasta el cierre de la Etapa 5."""
    with _cliente(tmp_path, monkeypatch) as cliente:
        respuesta = cliente.get("/clasico/")

    assert respuesta.status_code == 200
    assert "Control Taller" in respuesta.text
    assert "localhost:8000" in respuesta.text


def test_raiz_entrega_el_tablero_nuevo(tmp_path, monkeypatch):
    """La raíz entrega el tablero nuevo, con Vue local y sin abrir file://."""
    with _cliente(tmp_path, monkeypatch) as cliente:
        respuesta = cliente.get("/")
        vue = cliente.get("/vendor/vue/vue.global.prod.min.js")

    assert respuesta.status_code == 200
    assert "vendor/vue/vue.global.prod.min.js" in respuesta.text
    assert "Control Taller" not in respuesta.text
    assert vue.status_code == 200
