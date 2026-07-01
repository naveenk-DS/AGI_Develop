import pytest
from navix.config.settings import Settings

def test_settings_defaults():
    # Test that default configuration loads without errors
    config = Settings()
    assert config.app_name == "NAVIX AI Operating System"
    assert isinstance(config.ollama_url, str)
    assert config.ollama_url.startswith("http")
    assert config.qdrant_port == 6333
    assert config.environment in ["development", "production", "testing"]

def test_environment_validation():
    import os
    os.environ["ENVIRONMENT"] = "invalid_env"
    with pytest.raises(Exception):
        Settings()
    
    os.environ["ENVIRONMENT"] = "testing"
    config = Settings()
    assert config.environment == "testing"
