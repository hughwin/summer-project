import os

import bot
import settings


def main():
    with open(str(settings.BASE_DIRECTORY / "gcp_cred.json"), "w") as file:
        file.write(os.getenv("GCP_CRED"))
    bot.start_bot()


if __name__ == "__main__":
    main()
