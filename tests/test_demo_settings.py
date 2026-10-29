import os

import pytest

pytest.importorskip("temporalio")

from mcpkart.demo_run import temporal_settings


@pytest.fixture
def cloud_env(tmp_path, monkeypatch):
    for key in ("TEMPORAL_NAMESPACE", "TEMPORAL_ADDRESS", "TEMPORAL_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    path = tmp_path / ".env"
    path.write_text(
        "TEMPORAL_NAMESPACE=mcpkart-dev.iuiaz\n"
        "TEMPORAL_ADDRESS=temporal.example:7233\n"
        "TEMPORAL_API_KEY=temporal-test-placeholder\n"
        "OPENROUTER_API_KEY=openrouter-test-placeholder\n"
    )
    return path


def test_cloud_settings_read_private_file_without_exporting_model_key(cloud_env):
    options = temporal_settings(cloud_env)
    assert options["namespace"] == "mcpkart-dev.iuiaz"
    assert options["target_host"] == "temporal.example:7233"
    assert options["api_key"] == "temporal-test-placeholder" and options["tls"]
    assert "OPENROUTER_API_KEY" not in os.environ


def test_local_overrides_do_not_send_cloud_key_to_local_server(cloud_env, monkeypatch):
    monkeypatch.setenv("TEMPORAL_NAMESPACE", "default")
    monkeypatch.setenv("TEMPORAL_ADDRESS", "127.0.0.1:7241")
    options = temporal_settings(cloud_env)
    assert options["target_host"] == "127.0.0.1:7241"
    assert options["api_key"] is None and not options["tls"]


def test_cloud_address_must_be_explicit(cloud_env):
    cloud_env.write_text("TEMPORAL_NAMESPACE=mcpkart-dev.iuiaz\nTEMPORAL_API_KEY=test-placeholder\n")
    with pytest.raises(ValueError, match="TEMPORAL_ADDRESS"):
        temporal_settings(cloud_env)
