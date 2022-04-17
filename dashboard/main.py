import asyncio
from collections import deque, defaultdict
from functools import partial
from os import getenv

import aiohttp
import pandas as pd
import streamlit as st

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

                windows["graph"].append(data[3])
                windows["map"].append({"lat": data[5], "lon": data[6]})

                for column_name, graph in graphs.items():
                    await asyncio.sleep(0.1)
                    sensor_data = {column_name: windows[column_name]}
                    if column_name == "value":
                        graph.write(data)
                    if column_name == "graph":
                        graph.line_chart(sensor_data)
                    if column_name == "map":
                        df = pd.DataFrame(
                            [i for i in list(sensor_data["map"]) if i != 0]
                        )
                        graph.map(df, zoom=0)


st.set_page_config(page_title="stream", layout="wide")

status = st.empty()
connect = st.checkbox("Connect to WS Server")

col_names = ["value", "graph", "map"]
columns = [col.empty() for col in st.columns(3)]

window_size = st.number_input("Window Size", min_value=10, max_value=100)

if connect:
    asyncio.run(consumer_airquality(dict(zip(col_names, columns)), window_size, status))
else:
    status.subheader(f"Disconnected.")
