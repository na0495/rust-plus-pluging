import os

from dotenv import dotenv_values


class ConfigError(Exception):
    pass


REQUIRED_FIELDS = {
    "RUST_SERVER_IP": "server_ip",
    "RUST_SERVER_PORT": "server_port",
    "RUST_PLAYER_ID": "player_id",
    "RUST_PLAYER_TOKEN": "player_token",
    "DISCORD_WEBHOOK_URL": "webhook_url",
}


def load_config(env_path: str = ".env") -> dict:
    # Load from .env file first, then override with real env vars (for Docker)
    values = dotenv_values(env_path)
    values.update({k: v for k, v in os.environ.items() if k in REQUIRED_FIELDS})

    config = {}
    for env_key, config_key in REQUIRED_FIELDS.items():
        value = values.get(env_key, "").strip()
        if not value:
            raise ConfigError(
                f"Missing required config: {env_key}. "
                f"Check your .env file."
            )
        config[config_key] = value

    config["player_id"] = int(config["player_id"])
    return config
