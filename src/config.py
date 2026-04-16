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
    values = dotenv_values(env_path)

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
