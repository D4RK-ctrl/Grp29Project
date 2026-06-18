import asyncio
import queue as thread_queue


class StreamQueue:
    """A thread-safe queue that bridges the agent's background-thread event loop
    and the WebSocket's main event loop.

    The agent thread calls `await put(item)` (which is really a non-blocking,
    thread-safe enqueue). The WebSocket coroutine calls `await get()`, which
    polls the underlying thread-safe queue without blocking the event loop.
    """

    def __init__(self):
        self._q: thread_queue.Queue = thread_queue.Queue()
        self.done: bool = False

    async def put(self, item: dict):
        # thread_queue.Queue is thread-safe and not bound to any event loop,
        # so this works from the background agent thread.
        self._q.put_nowait(item)

    async def get(self) -> dict:
        # Poll the thread-safe queue cooperatively so we never block the loop.
        while True:
            try:
                return self._q.get_nowait()
            except thread_queue.Empty:
                await asyncio.sleep(0.15)
