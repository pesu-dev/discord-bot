import os
import discord
import subprocess
import utils.general as ug
from discord import app_commands
from discord.ext import commands


class SlashDev(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client


    @staticmethod
    def is_botdev():
        def predicate(interaction: discord.Interaction) -> bool:
            return any(role.id == ug.load_config_value("botDev") for role in interaction.user.roles)
        return app_commands.check(predicate)
    
    # will be transitioned to mod.py later
    @app_commands.command(name="echo", description="Echoes a message to the target channel")
    @app_commands.describe(channel="The channel to send the message to", message="The message to send", attachment="An optional attachment to send with the message")
    @is_botdev()
    async def echo(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str, attachment: discord.Attachment =None):
        await interaction.response.defer()
        if not attachment:
            await channel.send(message)
        else:
            await channel.send(message, file = await attachment.to_file())
        await interaction.followup.send(f"Message sent to {channel.mention}")

    @echo.error
    async def echo_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.followup.send(
                "Not to you lol", ephemeral=True
            )
        elif isinstance(error, app_commands.CommandInvokeError):
            if isinstance(error.original, discord.Forbidden):
                await interaction.followup.send(
                    "I do not have permission to send messages in that channel", ephemeral=True
                )
            elif isinstance(error.original, discord.NotFound):
                await interaction.followup.send(
                    "The specified channel does not exist", ephemeral=True
                )
            else:
                await interaction.followup.send(embed=ug.build_unknown_error_embed(error.original))
        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
    
    @app_commands.command(name="gitpull", description="Pulls the latest changes from the git repository")
    async def gitpull(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # can only be run by Han or rowletowl
        if interaction.user.id in ug.load_config_value("superUsers"):
            try:
                result = subprocess.run(
                    ["git", "pull"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                await interaction.followup.send(f"Git pull successful:\n{result.stdout}")
            except subprocess.CalledProcessError as e:
                await interaction.followup.send(f"Git pull failed:\n{e.stderr}")
        else:
            await interaction.followup.send(
                "You are not authorised to run this command", ephemeral=True
            )

    @gitpull.error
    async def gitpull_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
        

async def setup(client: commands.Bot):
    await client.add_cog(
        SlashDev(client), guild=discord.Object(id=os.getenv("GUILD_ID"))
    )
