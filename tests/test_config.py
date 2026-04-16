import os
import pytest
from unittest.mock import patch

from src.config import load_config, ConfigError


class TestLoadConfig:
    def test_loads_all_required_fields(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RUST_SERVER_IP=192.168.1.1\n"
            "RUST_SERVER_PORT=28015\n"
            "RUST_PLAYER_ID=76561198000000000\n"
            "RUST_PLAYER_TOKEN=mytoken123\n"
            "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abc\n"
        )
        config = load_config(str(env_file))
        assert config["server_ip"] == "192.168.1.1"
        assert config["server_port"] == "28015"
        assert config["player_id"] == 76561198000000000
        assert config["player_token"] == "mytoken123"
        assert config["webhook_url"] == "https://discord.com/api/webhooks/123/abc"

    def test_raises_on_missing_field(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "RUST_SERVER_IP=192.168.1.1\n"
            "RUST_SERVER_PORT=28015\n"
        )
        with pytest.raises(ConfigError, match="RUST_PLAYER_ID"):
            load_config(str(env_file))

    def test_raises_on_empty_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("")
        with pytest.raises(ConfigError):
            load_config(str(env_file))
