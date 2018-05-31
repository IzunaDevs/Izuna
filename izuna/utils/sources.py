import asyncio
import audioop
import functools
import tempfile

import discord
import youtube_dl as ytdl

from izuna.utils import http
from izuna.utils.music import DL_OPTS


class FFmpegAudio(discord.FFmpegPCMAudio):
    def __init__(self, file):
        self.file = file
        super().__init__(file, pipe=True)

    def cleanup(self):
        self.file.close()
        super().cleanup()


class YTDLSource(discord.AudioSource):
    def __init__(self, query, volume=1.0, loop=None, executor=None):
        self.query = query
        self.volume = volume
        self.executor = executor
        self.loop = loop or asyncio.get_event_loop()
        self._done = False

        self.source = None
        self.duration = None
        self.url = None
        self.id = None
        self.raw_url = None
        self.views = None
        self.likes = None
        self.dislikes = None
        self.is_stream = None
        self.uploader = None
        self.thumbnail = None
        self.title = None
        self.description = None
        self.tags = None
        self.requester = None
        self.request_id = None

    def __repr__(self):
        return (f"YTDLSource(title={self.title:r}, "
                f"url={self.url:r}, volume={self.volume})")

    async def load(self):
        with ytdl.YoutubeDL(DL_OPTS) as dl:
            f = functools.partial(dl.extract_info, self.query, download=False)

            data = await self.loop.run_in_executor(self.executor, f)
            if "entries" in data:
                data = data["entries"][0]
            self.set_data(data)

    async def load_data(self, executor=None):
        if not self._done and not self.is_stream:
            self._done = True
            with ytdl.YoutubeDL(DL_OPTS) as dl:
                f = functools.partial(dl.extract_info, self.query, download=False)
                data = await self.loop.run_in_executor(executor, f)
                if "entries" in data:
                    data = data["entries"][0]
                b = await http.get(data["url"], attribute="read")
                del data
                file = tempfile.TemporaryFile()
                file.write(b)
                file.flush()
                file.seek(0)
                self.source = FFmpegAudio(file)

    def set_data(self, data):
        self.duration = data.get("duration")
        self.url = data.get("webpage_url")
        self.id = data.get("id")
        self.raw_url = data.get("url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.is_stream = data.get("is_live")
        self.uploader = data.get("uploader")
        self.thumbnail = data.get("thumbnail")
        self.title = data.get("title")
        self.description = data.get("description")
        self.tags = data.get("tags")

    def read(self):
        return audioop.mul(self.source.read(), 2, self.volume)

    def cleanup(self):
        if hasattr(self, "source"):
            self.source.cleanup()

    def set_requester(self, requester):
        self.requester = requester
        self.request_id = requester.id


class OverlaySource(discord.AudioSource):
    def __init__(self, source, overlay, player, *, vc):
        self.source = source
        self.player = player
        self._overlay_source = overlay
        self.vc = vc
        self.vol = 1
        self.vol_step = .1
        self._run = True

    def read(self):
        if not self._run:
            return b""

        source_data = self.source.read()
        overlay_data = self._overlay_source.read()

        if not source_data:
            self.player.source = self._overlay_source
            self.vc.source = self._overlay_source
            self.cleanup()
            return overlay_data

        if not overlay_data:
            self.player.source = self.source
            self.vc.source = self.source
            self._overlay_source.cleanup()
            return source_data

        source_data = audioop.mul(source_data, 2, self.vol * (1 - self.vol_step))
        overlay_data = audioop.mul(overlay_data, 2, self.vol * self.vol_step)

        self.vol_change_step()

        return audioop.add(source_data, overlay_data, 2)

    def cleanup(self):
        self.source.cleanup()

    def disable(self):
        self._run = False
        self.vc.source = self._overlay_source
        self.player.source = self._overlay_source
        self.cleanup()

    def vol_change_step(self):
        if self.vol_step < 1:
            self.vol_step += 0.05
        else:
            if self._run:
                self.disable()
