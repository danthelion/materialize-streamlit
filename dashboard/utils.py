import asyncio
from collections import defaultdict, deque
from functools import partial
from os import getenv

import aiohttp
import pandas as pd

if getenv("DOCKERIZED"):
    WS_CONN = "ws://fastapi:9999/airquality"
else:
    WS_CONN = "ws://localhost:9999/airquality"


async def consumer_airquality(graphs, window_size, status):
    windows = defaultdict(partial(deque, [0] * window_size, maxlen=window_size))

    async with aiohttp.ClientSession(trust_env=True) as session:
        status.subheader(f"Connecting to {WS_CONN}")
        async with session.ws_connect(WS_CONN) as websocket:
            status.subheader(f"Connected to: {WS_CONN}")
            async for message in websocket:
                data = message.json()

                windows["raw"].append(data[3])
                windows["graph"].append(data[4])
                windows["map"].append({"lat": data[5], "lon": data[6]})

                for column_name, graph in graphs.items():
                    await asyncio.sleep(0.1)
                    sensor_data = {column_name: windows[column_name]}
                    if column_name == "raw":
                        graph.write(data)
                    if column_name == "graph":
                        graph.line_chart(sensor_data)
                    if column_name == "map":
                        df = pd.DataFrame(
                            [i for i in list(sensor_data["map"]) if i != 0]
                        )
                        graph.map(df, zoom=0)
