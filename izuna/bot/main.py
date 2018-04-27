import os

from discord.ext.commands import when_mentioned_or
from kitsuchan.k2 import core


class Izuna(core.Bot):
    def __init__(self):
        super().__init__()
        self.load_config()

        self.command_prefix = when_mentioned_or(*self.config["prefix"])

        for file in os.listdir("izuna/cogs"):
            if file.endswith(".py"):
                try:
                    self.load_extension(f"izuna.cogs.{file[:-3]}")
                except Exception as err:  # pylint: disable=broad-except
                    print(f"Unable to load cog {file[:-3]:r}: {err}")
