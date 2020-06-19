import requests
import json


def main():
    print("Starting")
    r = requests.get("https://hostux.social/api/v1/timelines/public?limit=5")
    statuses = json.dumps(r.text)
    print(statuses)


if __name__ == "__main__":
    main()


