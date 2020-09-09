import os

import bot
import settings


def main():
    with open(str(settings.BASE_DIRECTORY / os.getenv("google-site-verification")), "w") as file:
        file.write("google-site-verification:" + os.getenv("google-site-verification"))
    bot.start_bot()


if __name__ == "__main__":
    main()
