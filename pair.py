"""
Helper script to capture Rust+ server pairing information.

Usage:
1. Run this script: python pair.py
2. In Rust, go to a Tool Cupboard or the Rust+ menu
3. Click "Pair with Server"
4. The script will print your server details and update .env automatically
"""

import json
import sys
import os

from rustplus import FCMListener


FCM_DATA_FILE = "fcm_credentials.json"


class PairingListener(FCMListener):
    def on_notification(self, obj, notification, data_message):
        print("\n=== SERVER PAIRING RECEIVED ===\n")
        print(json.dumps(notification, indent=2))

        body = notification.get("body", notification)
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = notification

        server_ip = body.get("ip", "")
        server_port = body.get("port", "")
        player_id = body.get("playerId", "")
        player_token = body.get("playerToken", "")

        if server_ip and player_token:
            print(f"\nServer IP:    {server_ip}")
            print(f"Server Port:  {server_port}")
            print(f"Player ID:    {player_id}")
            print(f"Player Token: {player_token}")

            # Update .env file
            webhook_url = ""
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        if line.startswith("DISCORD_WEBHOOK_URL="):
                            webhook_url = line.strip().split("=", 1)[1]

            with open(".env", "w") as f:
                f.write(f"RUST_SERVER_IP={server_ip}\n")
                f.write(f"RUST_SERVER_PORT={server_port}\n")
                f.write(f"RUST_PLAYER_ID={player_id}\n")
                f.write(f"RUST_PLAYER_TOKEN={player_token}\n")
                f.write(f"DISCORD_WEBHOOK_URL={webhook_url}\n")

            print("\n.env file updated! You can now run the bot.")
            print("Run: docker compose up -d")
        else:
            print("\nCouldn't parse server details from notification.")
            print("Raw notification data above — grab the values manually.")


def main():
    if not os.path.exists(FCM_DATA_FILE):
        print(f"Missing {FCM_DATA_FILE}!")
        print(f"Create it with your FCM credentials from the Chrome extension.")
        print(f"See README for details.")
        sys.exit(1)

    with open(FCM_DATA_FILE, "r") as f:
        fcm_details = json.load(f)

    print("Listening for Rust+ pairing notifications...")
    print("Go in-game and click 'Pair with Server' on a Tool Cupboard.")
    print("Press Ctrl+C to stop.\n")

    PairingListener(fcm_details).start()


if __name__ == "__main__":
    main()
