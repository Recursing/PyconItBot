from datetime import datetime, timedelta
import logging
from scraper import get_pycon_schedule


logger = logging.getLogger(__name__)


def next_events(text="", time=None):
    """
        Returns list of events at specified datetime
    """
    if time is None:
        time = datetime.now()
    schedule = get_pycon_schedule()
    today = time.day if time.month == 5 else -1  # TODO handle pycons on multiple months
    schedule.sort(key=lambda x: str(x["day"]) + x["time"])
    text = text.strip()
    current_minutes = time.minute + time.hour * 60
    found_something = False
    if text:
        for event in schedule:
            event_start_minutes = int(event["time"][:2]) * 60 + int(event["time"][2:])
            event_end_minutes = event_start_minutes + int(event["duration"])
            if event["day"] < today or (
                event["day"] == today and event_end_minutes < current_minutes
            ):
                continue
            if text.lower() in str(event).lower():
                found_something = True
                yield event
    if found_something:
        return
    for event in schedule:
        event_start = int(event["time"][:2]) * 60 + int(event["time"][2:])
        event_end_minutes = event_start + int(event["duration"])
        if event["day"] > today or (
            event["day"] == today and event_end_minutes >= current_minutes
        ):
            yield event


def formatted_event(event):
    template = (
        "<code>{hour}:{minute}</code> <a href='{url}'>{title}</a>\n"
        "{track} - {duration} minutes - {speakers}\n"
        "{short_abstract}\n"
        "Tags: {tags}"
    )
    speakers = event.get("speakers", [])
    speakers_text = " - ".join(
        [f'<a href="{s["url"]}">{s["name"]}</a>' for s in speakers]
    )
    tags = " - ".join("<code>" + tag + "</code>" for tag in event.get("tags", []))

    short_abstract = event.get("abstract", "")
    if len(short_abstract) > 100:
        short_abstract = short_abstract[:100] + "…"
    hour, minute = event.get("time")[:2], event.get("time")[2:]
    return template.format(
        minute=minute,
        hour=hour,
        duration=event.get("duration", ""),
        speakers=speakers_text or "No speakers",
        title=event.get("name", ""),
        url=event.get("url", ""),
        track=event.get("track", ""),
        short_abstract=short_abstract,
        tags=tags or "No tags",
    )


def get_current_events(time):
    current_minutes = time.minute + time.hour * 60
    schedule = get_pycon_schedule()
    current_events = []
    for event in schedule:
        event_start = int(event["time"][:2]) * 60 + int(event["time"][2:])
        event_end = event_start + int(event["duration"])
        if (
            time.day == event["day"]
            and current_minutes <= event_end
            and current_minutes >= event_start
        ):
            current_events.append(event)
    current_events.sort(key=lambda event: -event.get("duration"))
    return [formatted_event(event) for event in current_events]


def next_current_events(time):
    time, schedule = get_next_schedule(time)
    current_events_text = (
        f"<pre>Events at May {time.day}, {time.hour}:{time.minute:0<2}</pre>\n"
    )
    current_events_text += "\n\n".join(schedule)
    return time, current_events_text


def get_next_schedule(time):
    if time > datetime(2019, 5, 5, 18, 1, 0, 0):
        time = datetime(2019, 5, 5, 18, 0, 0, 0)

    current_events = get_current_events(time)
    if not current_events:
        time = time + timedelta(days=0, seconds=60 * (30 - time.minute % 30))
        current_events = get_current_events(time)
    while not current_events:
        time = time + timedelta(days=0, seconds=30 * 60)
        current_events = get_current_events(time)
    return time, current_events
