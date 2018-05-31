

class Queue:
    def __init__(self,
                 chunk_size=2,
                 max_chunks=-1,
                 max_per_user=-1,
                 unique=None,
                 silence_errors=False,
                 executor=None):
        self.size = chunk_size
        self.max = max_chunks
        self.user_max = max_per_user
        self.unique = unique
        self.silence_errors = silence_errors
        self.executor = executor
        self.items = []
        self.current = []

    def _error(self, err):
        if not self.silence_errors:
            raise Exception(err)

    @property
    def queue(self):
        r = self.current[:]
        for group in self.items:
            r += group
        return r

    def __len__(self):
        return len(self.queue)

    def __repr__(self):
        return ("Queue(entries={1}, chunk_size={0.size}, "
                "max_chunks={0.max}, per_user={0.user_max}, "
                "unique={0.unique}, silent={0.silence_errors})").format(self, len(self.queue))

    def show(self, source="title"):
        res = []
        for group in self.items:
            g = []
            for data in group:
                g.append({source: getattr(data, source), "request_id": data.request_id})
            res.append(g)
        return res

    async def add(self, items):
        errors = []
        for data in items:
            try:
                await self.append(data)
            except Exception as e:  # pylint: disable=broad-except
                errors[data.title] = e.args[0]
        return errors

    async def append(self, item):
        if len(self) <= 2:
            await item.load_data(self.executor)
        # print("Adding:", item)
        # === LOGIC ===
        # Basically, the first thing is to find the index of the user's
        # last song (since when they add something new, it should always be
        # added after their other songs)
        # This is achieved by iterating backwards through the current queue,
        # stopping the first time something by that user is found
        # Next, we iterate forward from that starting point.
        # For each song, we put the user that added it into a set.
        # We continue to move forward this way until we hit a user that
        # is already in the set. We stop here and insert the item.

        # For users A, B, and C, imagine starting queue ABCABCABCBBBBB

        # User A tries to put something in the queue
        #       v last A, start here
        # ABCABCABCBBBBB
        # B goes into the set
        # C goes into the set
        # B is already in the set, so the A gets added here
        # ABCABCABCABBBBB

        # data["requester"] should have the `id` attribute,
        # this could be e.g. a discord.Member
        id_ = item.request_id

        if not self.items:
            self.items.append([item])
            return

        if len(self.items) == self.max:
            self._error("Max queue chunks reached.")

        x = 0
        for chunk in self.items:
            if chunk[0].request_id == id_ and len(chunk) == self.size:
                x += 1

        if x == self.user_max:
            self._error("User reached maximum amount of chunks")

        # Check for dupes
        if self.unique is not None:
            for chunk in self.items:
                for item_u in chunk:
                    if getattr(item_u, self.unique) == getattr(item, self.unique):
                        self._error("Item already queued, `unique` key duplicate.")

        # Insert the data
        # print("Iterating backwards")
        for index, value in enumerate(reversed(self.items)):
            # print(index)
            if index == len(self.items) - 1 or value[0].request_id == id_:
                # we found the last item by us or
                # we have no items in the queue

                if value[0].request_id == id_ and len(value) < self.size:
                    # last item by us has a free space left
                    value.append(item)
                    return

                # index to start from
                # python is 0-indexed so subtract 1
                start = len(self.items) - index - 1
                found_ids = []

                # Easier than `enumerate` in this case
                # print("Iterating forward")
                while True:
                    # print(start)
                    if start >= len(self.items):
                        # print("Inserting at the end")
                        # No place left, put it at the end
                        self.items.append([item])
                        return

                    id_ = self.items[start][0].request_id

                    if id in found_ids:
                        # print("Duplicate found, inserting")
                        # this id appears for the second time now
                        # so insert here
                        self.items.insert(start, [item])
                        return

                    # Add the id to the list
                    found_ids.append(id)

                    start += 1

    async def pop(self):
        if len(self) > 2:
            await self.queue[2].load_data(self.executor)
        if not self.current:
            # Load the next chunk
            # we use `pop` to make sure it disappears from the original list
            # because otherwise people could queue up forever
            self.current = self.items.pop(0)
        return self.current.pop(0)

    def clear(self):
        for i in self.queue:
            i.cleanup()
        self.items.clear()
        self.current.clear()

    def shuffle(self, requester):
        s = []
        for i, chunk in enumerate(self.items):
            if chunk[0].requester == requester:
                random.shuffle(chunk)  # shuffle chunk items
                s.append(i)

        # shuffle chunks around
        s_c = s[:]
        random.shuffle(s_c)
        queue = self.items[:]
        for i in s:
            queue[i] = self.items[s_c[i]]

        self.items = queue

    def cleanup(self):
        for i in self.queue:
            i.cleanup()