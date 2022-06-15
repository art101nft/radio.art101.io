# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2021, dsc@xmr.pm

from typing import List, Optional
import os
import logging
import asyncio

import discord
from quart import Quart

import settings
from ircradio.radio import Radio
from ircradio.utils import print_banner
from ircradio.youtube import YouTube
import ircradio.models

app = None
user_agents: List[str] = None
websocket_sessions = set()
download_queue = asyncio.Queue()
discord_bot = None
soap = Radio()
# icecast2 = IceCast2()


async def download_thing():
    global download_queue

    a = await download_queue.get()
    e = 1


async def _setup_icecast2(app: Quart):
    global icecast2
    await icecast2.write_config()


async def _setup_database(app: Quart):
    import peewee
    models = peewee.Model.__subclasses__()
    for m in models:
        m.create_table()


async def _setup_discord(app: Quart):
    global discord_bot
    loop = asyncio.get_event_loop()
    discord_bot = discord.Client(loop=loop)
    from ircradio.disco import start, message_worker
    start()

    asyncio.create_task(message_worker())


async def _setup_user_agents(app: Quart):
    global user_agents
    with open(os.path.join(settings.cwd, 'data', 'agents.txt'), 'r') as f:
        user_agents = [l.strip() for l in f.readlines() if l.strip()]


async def _setup_requirements(app: Quart):
    ls_reachable = soap.liquidsoap_reachable()
    if not ls_reachable:
        raise Exception("liquidsoap is not running, please start it first")


def create_app():
    global app, soap, icecast2
    app = Quart(__name__)
    app.logger.setLevel(logging.INFO)

    @app.before_serving
    async def startup():
        await _setup_requirements(app)
        await _setup_database(app)
        await _setup_user_agents(app)
        await _setup_discord(app)
        import ircradio.routes

        from ircradio.youtube import YouTube
        asyncio.create_task(YouTube.update_loop())

        print_banner()

    return app
