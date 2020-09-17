import json
import os

import bot
import settings


def main():
    # build gcp_cred.json file required for the functioning of GCP.
    # Hides keys on HEROKU.
    with open(str(settings.BASE_DIRECTORY / "gcp_cred.json"), "w") as file:
        credentials = json.loads(os.getenv("GCP_CRED"))
        json.dump(credentials, file)
    bot.start_bot()


if __name__ == "__main__":
    main()
