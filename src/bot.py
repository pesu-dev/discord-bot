import logging
from discord.ext import commands
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection
from pymongo import AsyncMongoClient
from typing import Optional


class DiscordBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_client: Optional[AsyncMongoClient] = None
        self.db: Optional[AsyncDatabase] = None
        self.link_collection: Optional[AsyncCollection] = None
        self.student_collection: Optional[AsyncCollection] = None
        self.anonban_collection: Optional[AsyncCollection] = None
        self.mute_collection: Optional[AsyncCollection] = None
        self.startTime: float
        self.logger = logging.getLogger("discord.app")
