import os
import time
import logging
import discord
from discord import Intents
from discord.ext import commands
from pathlib import Path
from discord.app_commands import CommandTree
import motor.motor_asyncio as motor
from utils import general as ug
from dotenv import load_dotenv

load_dotenv()

client = commands.Bot(
    command_prefix=os.getenv("BOT_PREFIX"),
    help_command=None,
    intents=Intents().all(),
    tree_cls=CommandTree,
)

connection = ""

try:
    client.mongo_client = motor.AsyncIOMotorClient(os.getenv("MONGO_URI"), tz_aware=True)
    client.db = client.mongo_client[os.getenv("DB_NAME")]
    client.link_collection = client.db["Link"]
    client.student_collection = client.db["Student"]
    client.anonban_collection = client.db["AnonBan"]
    client.mute_collection = client.db["mute"]
    
    connection = "Connected to MongoDB"
except Exception as e:
    connection = f"Failed to connect to MongoDB: {e}"


@client.event
async def on_ready():
    client.startTime = time.time()
    logger = logging.getLogger("discord")
    logger.info(f"Logged in as {client.user.name} ({client.user.id})")
    logging.getLogger("discord.client").info(connection)

    # Load cogs
    for path in Path("cogs").rglob("*.py"):
        if path.name == "__init__.py":
            continue
        elif path.name.startswith("__"):
            continue

        cog = ".".join(path.with_suffix("").parts)
        try:
            await client.load_extension(cog)
            logging.getLogger("discord").info(f"Loaded {cog}")
        except Exception as e:
            logging.getLogger("discord").error(f"Failed to load {cog}: {e}")

    # Sync commands
    await client.tree.sync(guild=discord.Object(id=ug.load_config_value("GUILD", {}).get("ID")))
    logger.info("Synced commands")

    # Set status
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="you",
        )
    )
    logger.info("Set status")


    logger.info("Bot is ready")


client.run(os.getenv("BOT_TOKEN"))
