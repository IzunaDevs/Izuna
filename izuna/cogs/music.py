from discord.ext.commands import command

from izuna.utils.queue import Queue
from izuna.utils.music import lookup


class Music:
    def __init__(self):
        self.queue = Queue()

    @command()
    async def play(self, ctx, *, song: str):
        url = await lookup(ctx, song)
        if url is None:
            return

        self.queue.append(url)

        ctx.send("I added the song to the queue, desu~")
