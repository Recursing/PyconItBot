from urllib.request import urlopen
from bs4 import BeautifulSoup
from json import dump, load
from urllib.error import HTTPError
from config import FIRST_DAY, SCHEDULE_URL


def cached_download(url):
    try:
        with open("schedule.html", "rb") as saved_source:
            return saved_source.read()
    except FileNotFoundError:
        source = urlopen(url).read()
        with open("schedule.html", "wb") as saved_source:
            saved_source.write(source)
        return source


def get_abstract(url):
    url = url.rstrip("/")
    url += ".xml"
    try:
        soup = BeautifulSoup(urlopen(url).read().decode())
        abstract = soup("abstract")
        if abstract and abstract[0]("p"):
            return "\n".join(e.text for e in soup("abstract")[0]("p"))
        elif abstract:
            return abstract[0].text
        else:
            print(f"Abstract not found for {url}")
            return ""
    except HTTPError as e:
        print(e)
        print(url)
        return ""


def parse_schedule(source):
    soup = BeautifulSoup(source, "html.parser")
    schedule = []
    days = [soup.find(id="day{}".format(i)) for i in range(4)]
    for day_num, day in enumerate(days):
        track_names = {}
        track_headers = day.findAll("div", {"class": "schedule__header--track"})
        for track_header in track_headers:
            track_names[track_header["data-track"]] = track_header.text.strip()

        for event_tag in day.findAll("div", {"class": "event"}):
            event = {}
            tag_classes = event_tag.get("class", [])
            for tag_class in tag_classes:
                if tag_class.startswith("duration-"):
                    event["duration"] = int(tag_class.replace("duration-", ""))
                elif tag_class.startswith("time-"):
                    event["time"] = tag_class.replace("time-", "")

            event["track"] = track_names[event_tag.parent["data-track"]]
            speakers_tag = event_tag.find("div", {"class": "speakers"})
            if speakers_tag:
                speakers = []
                for speaker_tag in speakers_tag.findAll("a"):
                    name = speaker_tag.text.strip()
                    url = "https://www.pycon.it" + speaker_tag["href"]
                    speakers.append({"name": name, "url": url})
                event["speakers"] = speakers
            name_tag = event_tag.find("h3", {"class": "name"})
            if name_tag.find("a"):
                event["name"] = name_tag.find("a").text.strip()
                if name_tag.find("a")["href"] != "#":
                    href = name_tag.find("a")["href"]
                    if not href.startswith("http"):
                        href = "https://www.pycon.it" + href
                    print(href)
                    event["url"] = href
                    event["abstract"] = get_abstract(href)
            else:
                event["name"] = " ".join(name_tag.text.strip().split())
            tags = event_tag.findAll("a", {"class": "tag"})
            if tags:
                event["tags"] = [t.text.strip() for t in tags]
            status_bar = event_tag.find("a", {"class": "status-bar"})
            if status_bar:
                level_tag = status_bar.find("span", {"class": "maximized"})
                if level_tag:
                    event["level"] = level_tag.text.strip()
            event["day"] = day_num + FIRST_DAY
            schedule.append(event)
    with open("schedule.json", "w") as out_file:
        dump(schedule, out_file, indent=2)
    return schedule


def get_pycon_schedule():
    try:
        with open("schedule.json", "r") as saved_source:
            return load(saved_source)
    except FileNotFoundError:
        return parse_schedule(cached_download(SCHEDULE_URL))
