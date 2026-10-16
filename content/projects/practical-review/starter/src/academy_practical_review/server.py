from collections.abc import Iterator
from contextlib import contextmanager
import socket
from threading import Thread
import time
from fastapi import FastAPI
import uvicorn


@contextmanager
def serving(app: FastAPI) -> Iterator[str]:
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(64)
    server = uvicorn.Server(
        uvicorn.Config(
            app, log_level="critical", access_log=False, lifespan="off", timeout_graceful_shutdown=2
        )
    )
    worker = Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    worker.start()
    try:
        end = time.monotonic() + 5
        while not server.started:
            if not worker.is_alive() or time.monotonic() >= end:
                raise RuntimeError("local server startup failed")
            time.sleep(0.01)
        yield "http://127.0.0.1:" + str(listener.getsockname()[1])
    finally:
        server.should_exit = True
        worker.join(5)
        listener.close()
        if worker.is_alive():
            raise RuntimeError("local server did not finish")
