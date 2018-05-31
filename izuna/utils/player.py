import discord


class Player:
    def __init__(self, channel: discord.VoiceChannel, queue):
        self.channel = channel
        self.queue = queue
        self.vc = None
        self.source = None

    def start(self):
        self.vc = self.channel.connect(reconnect=True)
        self.vc.play(self.source)
