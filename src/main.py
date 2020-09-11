import json
import os

import bot
import settings


def main():
    with open(str(settings.BASE_DIRECTORY / "gcp_cred.json"), "w") as file:
        json.load(os.getenv("GCP_CRED"), file)
    with open(str(settings.BASE_DIRECTORY / 'gcp_cred.json'), 'r') as f:
        data = json.load(f)
    print(data)
    bot.start_bot()


if __name__ == "__main__":
    main()
