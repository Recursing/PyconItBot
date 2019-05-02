from datetime import datetime, timedelta
import itertools
from schedule import next_events, next_current_events
from telebot import TeleBot, types
from telebot.apihelper import ApiException
from config import TOKEN, FIRST_DAY

bot = TeleBot(TOKEN)


@bot.inline_handler(func=None)
def list_events(inline_query):
    """
        Returns a message with a view of the current pycon schedule,
        Html formatted text with the current events and buttons to navigate
        the schedule at other times and days
    """
    # PyData: titolo - Speaker, Speaker - 45min
    # button('text', on_click=update_schedule)  # text caso tipico nuovo testo
    events = itertools.islice(next_events(text=inline_query.query), 20)
    results = [message_from_event(e) for e in events]

    inline_results = []
    for i, r in enumerate(results):
        ir = types.InlineQueryResultArticle(
            id=i,
            title=r["title"],
            description=r["description"],
            input_message_content=types.InputTextMessageContent(
                r["text"][:4096], parse_mode="HTML"
            ),
        )
        inline_results.append(ir)
    bot.answer_inline_query(
        inline_query.id,
        inline_results,
        switch_pm_text="Show me full schedule",
        switch_pm_parameter="fullschedule",
    )


@bot.callback_query_handler(func=None)
def update_schedule(callback_query):
    day, hour, minute = [int(e) for e in callback_query.data.split("x")]
    time = datetime(2019, 5, day, hour, minute, 0, 0)
    time, current_events_text = next_current_events(time)
    try:
        bot.edit_message_text(
            current_events_text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=get_keyboard(time),
            parse_mode="HTML",
        )
    except ApiException:
        pass


@bot.message_handler(commands=["start", "show_events"])
def show_events(message):
    time, current_events_text = next_current_events(datetime.now())
    bot.send_message(
        chat_id=message.from_user.id,
        text=current_events_text,
        parse_mode="HTML",
        reply_markup=get_keyboard(time),
    )


@bot.message_handler(commands=["help"])
def start_message(message):
    bot.send_message(message.from_user.id, "Send /show_events to see the schedule")


def message_from_event(event):
    title = event["name"]
    desc_template = "{hour}:{minute} - {duration}m - {track}\n{abstract}"
    hour, minute = event.get("time")[:2], event.get("time")[2:]
    description = desc_template.format(
        hour=hour,
        minute=minute,
        duration=event.get("duration"),
        track=event.get("track"),
        abstract=event.get("abstract", "")[:200],
    )
    speakers = event.get("speakers", [])
    speakers_text = [f'<a href="{s["url"]}">{s["name"]}</a>' for s in speakers]
    tags = " - ".join("<code>" + tag + "</code>" for tag in event.get("tags", []))
    mesage_text = (
        "<code>May {day}, {hour}:{min}</code> <a href='{url}'>{title}</a>\n"
        "{track} track - {duration} minutes - {presenters}\n"
        "{abstract}\n"
        "Tags: {tags}"
    ).format(
        day=event["day"],
        min=minute,
        hour=hour,
        duration=event.get("duration"),
        presenters=" - ".join(speakers_text) or "No speakers",
        title=title,
        url=event.get("url", ""),
        track=event.get("track", ""),
        abstract=event.get("abstract", ""),
        tags=tags or "No Tags",
    )

    buttons = {
        "text": "Show parrallel events",
        "callback_data": f"{event['day']:0<2}x{hour}x{minute}",
    }
    return {
        "title": title,
        "description": description,
        "text": mesage_text,
        "buttons": buttons,
    }


def get_keyboard(time):
    inline_keyboard = types.InlineKeyboardMarkup()
    inline_keyboard.keyboard = generate_buttons(time)
    return inline_keyboard


def generate_buttons(time):
    nxt_time = time + timedelta(0, 30 * 60)
    prv_time = time - timedelta(0, 30 * 60)
    nxt_time_str = encode_time(nxt_time)
    prv_time_str = encode_time(prv_time)
    left_button = {"text": "-30 min", "callback_data": f"{prv_time_str}"}
    right_button = {"text": "+30 min", "callback_data": f"{nxt_time_str}"}
    # Skips first day, as there are no talks
    btn_days = [
        {
            "text": f"Day {i+1}",
            "callback_data": f"{encode_time(time.replace(day=(i+FIRST_DAY+1)))}",
        }
        for i in range(3)
    ]
    return [[left_button, right_button], btn_days]


def encode_time(time):
    return "x".join(f"{i:0>2}" for i in [time.day, time.hour, time.minute])


print("polling")
print(bot.get_me())
bot.polling()
