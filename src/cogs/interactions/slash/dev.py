import os
import discord
import subprocess
import utils.general as ug
from discord import app_commands
from discord.ext import commands


class SlashDev(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        
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
