from collections import deque


class SequenceCache:
    """
    Keeps a rolling set of recently seen (frame_id, sequence, sender_id) tuples
    to prevent duplicate processing during retries or repeated forwards.
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._queue = deque()
        self._set = set()

    def _key(self, frame_id: int, sequence: int, sender_id: int) -> tuple[int, int, int]:
        return (frame_id, sequence, sender_id)

    def contains(self, frame_id: int, sequence: int, sender_id: int) -> bool:
        return self._key(frame_id, sequence, sender_id) in self._set

    def add(self, frame_id: int, sequence: int, sender_id: int) -> None:
        key = self._key(frame_id, sequence, sender_id)

        if key in self._set:
            return

        self._queue.append(key)
        self._set.add(key)

        while len(self._queue) > self.max_size:
            old = self._queue.popleft()
            self._set.remove(old)
