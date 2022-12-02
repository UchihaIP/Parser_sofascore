import json
import time
from datetime import date
from typing import Any

from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
import requests

import db_session

BASE_URL = "https://api.sofascore.com/"


def parse_matches(sports: list) -> list[dict[str, str | Any]]:
    matches = []
    today = date.today().strftime("%Y-%m-%d")
    count_id = 0
    for sport in sports:
        routes = [f"{BASE_URL}api/v1/sport/{sport}/events/live",
                  f'{BASE_URL}api/v1/sport/{sport}/scheduled-events/{today}'
                  ]
        for url in routes:
            response = requests.get(url=url)
            data = json.loads(response.text)
            flag = "False"
            if routes[0] == url:
                flag = "True"
            for event in data["events"]:
                matches.append({
                    "_id": count_id,
                    "sport": sport,
                    "tournament": event["tournament"]["name"],
                    "home_team": event["homeTeam"]["name"],
                    "away_team": event["awayTeam"]["name"],
                    "home_score": event["homeScore"].get("current"),
                    "away_score": event["awayScore"].get("current"),
                    "live": flag}
                )
                count_id += 1

    return matches


def get_sports() -> list:
    """Gets a list of sports"""
    response = requests.get(url="https://api.sofascore.com/api/v1/sport/10800/event-count")
    sport_type = [sport_key for sport_key in response.json()]
    return sport_type


def _insert_document(collection: Collection, data: list):
    return collection.insert_many(data)


def find_document(collection: Collection, status: dict) -> list[dict]:
    result = collection.find(status)
    return [r for r in result]


def main() -> None:
    if len(find_document(db_session.sofa_collection, {})) == 0:
        begin = time.time()
        print("Start parsing SofaScore.com")
        _sports = get_sports()
        matches_data = parse_matches(_sports)
        print("End parse")
        try:
            _insert_document(db_session.sofa_collection, matches_data)
        except DuplicateKeyError:
            raise "There are already such records in the database"
        print(f"All data has been added to the database! In {time.time() - begin}")

    while True:
        status = str(input("What data should be shown? Live or All?")).strip().lower()
        if status in ("live", "all"):
            break
    if status == "live":
        result = find_document(db_session.sofa_collection, {"live": "True"})
        with open("live_results.json", "w", encoding="utf-8") as wr:
            json.dump(result, wr, ensure_ascii=False, indent=4)
    elif status == "all":
        result = find_document(db_session.sofa_collection, {"live": "False"})
        with open("all_results.json", "w", encoding="utf-8") as wr:
            json.dump(result, wr, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
