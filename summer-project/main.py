import requests
import json


def main():
    print("Starting")
    r = requests.get("https://hostux.social/api/v1/timelines/public?limit=5")
    statuses = r.json()
    print(statuses[0])
    print(statuses[1])

if __name__ == "__main__":
    main()


