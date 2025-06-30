import os
import discord
from discord.ext import commands


class Events(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    """    client.tree.error(coro = self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        self.client.dispatch("app_command_error", interaction, error)

    @commands.Cog.listener("on_app_command_error")
    async def get_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if interaction.response.is_done():
            return
        else:
            await interaction.response.send_message(
                f"An error occurred while processing the command: {error} and the type of error is {type(error)}",
                ephemeral=False
            )"""

    """
    async def get_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
		pass # process exception here"""

    # this is for now a really useless cog for events.

    


async def setup(client: commands.Bot):
    await client.add_cog(Events(client), guild=discord.Object(id=os.getenv("GUILD_ID")))
