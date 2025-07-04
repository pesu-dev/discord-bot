import os
import time
import logging
import discord
import json
from discord import Intents
from discord.ext import commands
from pathlib import Path
from discord.app_commands import CommandTree
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

p = Path(__file__).parent / "cogs" / "config.json"
if not p.exists():
    print("config.json not found")
    exit(1)
config = json.load(open(p))

client = commands.Bot(
    command_prefix=os.getenv("BOT_PREFIX"),
    help_command=None,
    intents=Intents().all(),
    tree_cls=CommandTree,
)

client.config = config


@client.event
async def on_ready():
    await client.wait_until_ready()
    client.startTime = time.time()
    logger = logging.getLogger("discord")
    logger.info(f"Logged in as {client.user.name} ({client.user.id})")

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

    # Set status
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="you",
        )
    )
    logger.info("Set status")

    logger.info("Bot is ready")


@client.command(name='reload', help='To reload all cogs.')
async def reload(ctx, cog="all"):
    # Check if the user not an admin or mod or senior bot dev
    role_lst = [role.id for role in ctx.author.roles]
    if not any(role in role_lst for role in [config["roles"]["admin"], config["roles"]["mod"],
                                             config["roles"]["senior_bot_developer"]]):
        await ctx.reply("Noob you can't do that")
        return
    # Reload cogs
    if cog == "all":
        for root, dirs, files in os.walk("cogs"):
            for f in files:
                if f.endswith(".py"):
                    root = root.replace('/', '.').replace('\\', '.')
                    cog = f"{root}.{f[:-3]}"
                    await client.reload_extension(cog)
                    logger.info(f"Reloaded {cog}")
        await ctx.reply("Reloaded!")
    else:
        if cog.endswith('.py'):
            cog = cog[:-3]
        if not cog.startswith('cogs.'):
            cog = "cogs." + cog
        try:
            await client.reload_extension(cog)
            logger.info(f"Reloaded {cog}")
            await ctx.reply("Reloaded " + cog)
        except commands.ExtensionNotLoaded:
            await ctx.reply("Cog not found")


@client.command(name='sync', help='To sync all commands.')
async def sync(ctx):
    # Check if the user not an admin or mod or senior bot dev
    role_lst = [role.id for role in ctx.author.roles]
    if not any(role in role_lst for role in [config["roles"]["admin"], config["roles"]["mod"],
                                             config["roles"]["senior_bot_developer"]]):
        await ctx.reply("Noob you can't do that")
        return
    # Sync commands
    await client.tree.sync(guild=discord.Object(id=client.config['guild_id']))
    logger.info("Synced commands")
    await ctx.reply('Synced!')

client.run(os.getenv("BOT_TOKEN"))
