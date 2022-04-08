import requests
import argparse

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
from enum import Enum
from mail import Emailer


class SupportedFacilities(str, Enum):
    Elisabeth = "Elisabeth"
    PoterneDesPeupliers = "Poterne des Peupliers"


@dataclass
class TimeSlot:
    start: int
    end: int
    facility: str
    court: int
    date: datetime

    def __str__(self) -> str:
        date = self.date.strftime("%d/%m/%Y")
        return f"{date} {self.start}h-{self.end}h {self.facility} Court {self.court}"


def parse_date(date_string: str) -> datetime:
    return datetime.strptime(date_string, "%Y-%m-%d")


def get_available_timeslots(date: datetime, facility: str) -> List[TimeSlot]:
    url = "https://tennis.paris.fr/tennis/jsp/site/Portal.jsp?page=recherche&action=ajax_load_planning"

    facility_formatted = "+".join(facility.split())

    payload = f"date_selected={date.day:02}%2F{date.month:02}%2F{date.year}&name_tennis={facility_formatted}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    timeslots = []
    if response.status_code == 200:
        parsed_html = BeautifulSoup(response.text, features="html.parser")

        rows = parsed_html.find_all("table")[0].find_all("tr")

        for row in rows[2:]:
            cells = row.find_all("td")
            t = cells[0].text.split()
            t1, t2 = int(t[0][:2]), int(t[2][:2])

            for court, cell in enumerate(cells):
                if cell.find_all("span", text="LIBRE"):
                    timeslots.append(
                        TimeSlot(
                            start=t1, end=t2, facility=facility, court=court, date=date,
                        )
                    )

    return timeslots


def scan_next_week(
    minimum_start_time_weekday: int, minimum_start_time_weekend
) -> List[TimeSlot]:
    result = []
    today = datetime.today()
    for i in range(1, 7):
        date = today + timedelta(days=i)

        if date.weekday() in [5, 6]:
            minimum_start_time = minimum_start_time_weekend
        else:
            minimum_start_time = minimum_start_time_weekday

        for facility in SupportedFacilities:
            timeslots = get_available_timeslots(date, facility)
            for timeslot in timeslots:
                if timeslot.start >= minimum_start_time:
                    result.append(timeslot)
    return result


def format_timeslots(timeslots: List[TimeSlot]) -> str:
    body = "Available timeslots:\n\n"
    for timeslot in timeslots:
        body += f"{timeslot}\n"
    body += "\nLink to reserve: https://tennis.paris.fr/tennis/jsp/site/Portal.jsp?page=recherche&action=rechercher_creneau"
    return body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--minimum-start-time-weekday",
        type=int,
        help="Minimum starting hour for weekdays",
        default=20,
    )
    parser.add_argument(
        "--minimum-start-time-weekend",
        type=int,
        help="Minimum starting hour for weekends",
        default=12,
    )
    parser.add_argument(
        "--mail-config",
        type=str,
        help="Path to mail configuration file",
        default="mail_config.yml",
    )
    args = parser.parse_args()

    timesolts = scan_next_week(
        args.minimum_start_time_weekday, args.minimum_start_time_weekend
    )

    emailer = Emailer(args.mail_config)
    emailer.send_email(
        "Hurray! Tennis courts are available!", format_timeslots(timesolts)
    )


if __name__ == "__main__":
    main()
