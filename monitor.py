import requests
import argparse

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
from enum import Enum


class SupportedCourts(str, Enum):
    Elisabeth = "Elisabeth"
    PoterneDesPeupliers = "Poterne des Peupliers"


@dataclass
class TimeSlot:
    start: int
    end: int
    court: str
    date: datetime

    def __str__(self) -> str:
        return (
            f"{self.date.strftime('%Y-%m-%d')} {self.start}h-{self.end}h {self.court}"
        )


def parse_date(date_string: str) -> datetime:
    return datetime.strptime(date_string, "%Y-%m-%d")


def get_available_timeslots(date: datetime, court: str) -> List[TimeSlot]:
    url = "https://tennis.paris.fr/tennis/jsp/site/Portal.jsp?page=recherche&action=ajax_load_planning"

    court_formatted = "+".join(court.split())

    payload = f"date_selected={date.day:02}%2F{date.month:02}%2F{date.year}&name_tennis={court_formatted}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        parsed_html = BeautifulSoup(response.text, features="html.parser")

        free_timeslots = parsed_html.tbody.find_all("span", text="LIBRE")
        timeslots = []
        for free_timeslot in free_timeslots:
            timeslot_text = free_timeslot.parent.parent.find("td").text
            t = timeslot_text.split()
            t1, t2 = int(t[0][:2]), int(t[2][:2])
            timeslot = TimeSlot(t1, t2, court, date)
            timeslots.append(timeslot)

        return timeslots

    return []


def scan_next_week(minimum_start_time: int) -> List[TimeSlot]:
    result = []
    today = datetime.today()
    for i in range(1, 7):
        date = today + timedelta(days=i)
        for court in SupportedCourts:
            timeslots = get_available_timeslots(date, court)
            for timeslot in timeslots:
                if timeslot.start >= minimum_start_time:
                    result.append(timeslot)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--minimum-start-time", type=int, help="Minimum starting hour", required=True
    )
    args = parser.parse_args()

    for x in scan_next_week(args.minimum_start_time):
        print(x)


if __name__ == "__main__":
    main()
