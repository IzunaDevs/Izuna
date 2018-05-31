import functools

from youtube_dl import YoutubeDL

from izuna.utils.choose import choice

DL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "audioformat": "opus",
    "source_address": "0.0.0.0",
    "quiet": True,
    "default_search": "ytsearch10"
}

JOINER = " • "

BASE_MSG = f"""
While looking up that song, I found multiple songs, desu~
{JOINER}{{0}}
Please select a song from the list!
"""


async def lookup(ctx, song):
    func = functools.partial(YoutubeDL(DL_OPTS).extract_info, song, download=False)

    data = ctx.bot.loop.run_in_executor(None, func)

    if "entries" in data:
        entries = {entry["title"]: entry["url"] for entry in data["entries"]}

        question = BASE_MSG.format(JOINER.format(list(entries.keys())))

        return choice(ctx, entries, question)

    return data["url"]
