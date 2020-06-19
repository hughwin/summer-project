import requests


def main():
    print("Starting")
    r = requests.get("https://xkcd.com/1906/")
    print(r)
    print("Finished")


if __name__ == "__main__":
    main()


