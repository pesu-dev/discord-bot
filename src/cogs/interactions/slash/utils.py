import os
import discord
from discord import app_commands
from discord.ext import commands


class SlashGeneral(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="ping", description="Get the bot's latency")
    async def ping_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send(
            content=f"Pong!!!\nPing = `{round(self.client.latency * 1000)}ms`"
        )

    """
    @app_commands.command(name="crash", description="Purposely crash to test error handler")
    async def crash(self, interaction: discord.Interaction):
        # check if person has admin permissions or else raise permission error
        ch = ["adminerror", "valueerror"]
        if ch == "adminerror":
            if interaction.user.guild_permissions.administrator:
                raise app_commands.MissingPermissions(
                    missing_permissions=["administrator"]
                )        
        elif ch == "valueerror":
            raise ValueError("This is a value error for testing purposes.")
    @crash.error
    async def crash_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # check if it was a value error
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You do not have permission to use this command.", ephemeral=False
            )"""
    
    """
    .set(this.uptime, ["uptime", "ut"])
            .set(this.ping, ["ping", "tp"])
            .set(this.support, ["support", "contribute"])
            .set(this.count, ["count", "c"])
            .set(this.snipe, ["snipe"])
            .set(this.editsnipe, ["editsnipe"])
            .set(this.poll, ["poll"])
            .set(this.help, ["help", "h"])
            .set(this.addroles, ["roles", "ar"])
            .set(this.spotify, ["spotify"]) these are the commands"""
    
    


async def setup(client: commands.Bot):
    await client.add_cog(
        SlashGeneral(client), guild=discord.Object(id=os.getenv("GUILD_ID"))
    )
