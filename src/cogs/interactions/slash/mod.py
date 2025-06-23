import os
import discord
from discord import app_commands
from discord.ext import commands


class SlashMod(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    # under work by tachyon

async def setup(client: commands.Bot):
    await client.add_cog(
        SlashMod(client), guild=discord.Object(id=os.getenv("GUILD_ID"))
    )
