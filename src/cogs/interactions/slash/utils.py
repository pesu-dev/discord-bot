import os
import discord
import utils.general as ug
from discord import app_commands
from discord.ext import commands


class SlashUtils(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    

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
    
    @app_commands.command(name="ping", description="Get the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send(
            content=f"Pong!!!\nPing = `{round(self.client.latency * 1000)}ms`"
        )

    @ping.error
    async def ping_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))


    @app_commands.command(name="uptime", description="Get the bot's uptime")
    async def uptime(self, interaction: discord.Interaction):
        await interaction.response.defer()
        start = getattr(self.client, "startTime", None)
        if start is None:
            await interaction.followup.send(
                content="Uptime not available. Please restart the bot."
            )
        else:
            unixtmstmp = int(start)
            relative = f"<t:{unixtmstmp}:R>"
            longdatewithshorttime = f"<t:{unixtmstmp}:f>"

            await interaction.followup.send(content=f"Bot was started {relative}\ni.e., on {longdatewithshorttime}")
    
    @uptime.error
    async def uptime_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(name="support", description="Contribute to bot development")
    async def support(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send(
            content="You can contribute to the bot here\nhttps://github.com/nostorian/pesu-bot")
        
    @support.error
    async def support_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
        
    
    @staticmethod
    def get_verified_count(guild: discord.Guild) -> int:
        role = discord.utils.get(guild.roles, id=ug.load_config_value("verified"))
        if role is None:
            return 0
        return len(role.members)

    
    @app_commands.command(name="count", description="Get the number of servers the bot is in")
    @app_commands.describe(rolelist="List of roles to count members for, separated by &")
    async def count(self, interaction: discord.Interaction, rolelist: str = None):
        await interaction.response.defer()
        if rolelist is None:
            rolec = type(self).get_verified_count(interaction.guild)
            await interaction.followup.send(
                content=f"**Server Stats**\n"
                            f"Total number of people on the server: `{interaction.guild.member_count}`\n"
                            f"Total number of verified people: `{rolec}`\n"
                            f"Number of people that can see this channel: `{len(interaction.channel.members)}`\n"
                            f"Number of bots that can see this channel: `{len([m for m in interaction.channel.members if m.bot])}`\n"
                )
        else:
            roleList = [role.strip() for role in rolelist.split("&") if role.strip()]
            roleObjects = []
            for roleName in roleList:
                role = discord.utils.get(interaction.guild.roles, name=roleName)
                if role is not None:
                    roleObjects.append(role)
            

            if len(roleObjects) == 0:
                await interaction.followup.send(
                    content="No roles found. Processing request for server stats..."
                )
                rolec = type(self).get_verified_count(interaction.guild)
                await interaction.followup.send(
                    content=f"**Server Stats**\n"
                            f"Total number of people on the server: `{interaction.guild.member_count}`\n"
                            f"Total number of verified people: `{rolec}`\n"
                            f"Number of people that can see this channel: `{len(interaction.channel.members)}`\n"
                            f"Number of bots that can see this channel: `{len([m for m in interaction.channel.members if m.bot])}`\n"
                )
                
            else:   
                common_members = set(roleObjects[0].members)
                for role in roleObjects[1:]:
                    common_members &= set(role.members)
                
                memberCounts = len(common_members)

                roleNames = [role.name for role in roleObjects]
                wrd = "have" if memberCounts > 1 or memberCounts == 0 else "has"
                pluralorsingle = "people" if memberCounts > 1 or memberCounts == 0 else "person"
                await interaction.followup.send(content=f"{memberCounts} {pluralorsingle} {wrd} [{', '.join(roleNames)}]")


        
    

    @count.error
    async def uptime_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error)) 
    
    


async def setup(client: commands.Bot):
    await client.add_cog(
        SlashUtils(client), guild=discord.Object(id=os.getenv("GUILD_ID"))
    )
