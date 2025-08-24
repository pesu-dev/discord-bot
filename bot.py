import logging
from discord.ext import commands
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection
from pymongo import AsyncMongoClient


class DiscordBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_client: AsyncMongoClient
        self.db: AsyncDatabase
        self.link_collection: AsyncCollection
        self.student_collection: AsyncCollection
        self.anonban_collection: AsyncCollection
        self.mute_collection: AsyncCollection
        self.startTime: float
        self.logger = logging.getLogger("discord.app")
