import os
import time
import discord
from discord import app_commands
from discord.ext import commands
import motor.motor_asyncio as motor
from utils import general as ug

mongo_client = motor.AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("DB_NAME")]
link_collection = db["Link"]
student_collection = db["Student"]


class SlashLink(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="info", description="Get linking info about a user")
    @app_commands.describe(user="User to fetch info about")
    async def info(self, interaction: discord.Interaction, user: discord.Member):
        createdAt = user.created_at
        unixTimestamp = int(time.mktime(createdAt.timetuple()))
        joinedAt = user.joined_at
        unixJoinedTimestamp = int(time.mktime(joinedAt.timetuple())) if joinedAt else None
        
        embed = discord.Embed(title="User Info", color=0x48BF91)
        embed.set_thumbnail(url=user.display_avatar.url)
        
        embed.add_field(name="Name", value=user.name, inline=True)
        embed.add_field(name="ID", value=str(user.id), inline=True)
        embed.add_field(name="Creation", value=f"<t:{unixTimestamp}:R>", inline=True)
        
        if unixJoinedTimestamp:
            embed.add_field(name="Join", value=f"<t:{unixJoinedTimestamp}:R>", inline=True)

        await interaction.response.send_message(embed=embed)
        if ug.has_mod_permissions(interaction.user):
            newEmbed = discord.Embed(title="Priviliged Info", color=0x48BF91)
            linkRes = await link_collection.find_one({"userId": str(user.id)})

            if not linkRes:
                newEmbed.add_field(name="Status", value="This user is not linked yet", inline=False)
                return await interaction.followup.send(embed=newEmbed, ephemeral=True)

            if not linkRes.get("prn"):
                newEmbed.add_field(name="Error", value="Missing data!!!", inline=False)
                return await interaction.followup.send(embed=newEmbed, ephemeral=True)

            newEmbed.add_field(name="PRN", value=linkRes['prn'], inline=False)

            await interaction.followup.send(embed=newEmbed, ephemeral=True)


    @info.error
    async def info_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            if isinstance(error.original, discord.NotFound):
                await interaction.followup.send("The specified user does not exist or is not in the server", ephemeral=True)
            else:
                await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))


    @app_commands.command(name="delink", description="Remove a user's linking")
    @app_commands.describe(user="User to delink")
    async def delink(self, interaction: discord.Interaction, user: discord.Member):
        if not ug.has_mod_permissions(interaction.user):
            return await interaction.response.send_message("You are not authorised to run this command", ephemeral=True)

        await interaction.response.defer()
        result = await link_collection.delete_one({"userId": str(user.id)})
        if result.deleted_count == 0:
            return await interaction.followup.send("This user was not linked in the first place", ephemeral=True)
        
        roles_to_remove = []
        for role in user.roles:
            if role.id != interaction.guild.id:
                roles_to_remove.append(role)
 
        try:
            await user.remove_roles(*roles_to_remove, reason="Delinking")

            just_joined_role = interaction.guild.get_role(ug.load_config_value("just_joined"))
            if just_joined_role:
                await user.add_roles(just_joined_role)
        except discord.Forbidden:
            return await interaction.followup.send("I am unable to remove roles from this user although they were delinked. Please check my permissions", ephemeral=True)

        await interaction.followup.send(f"De-linked <@{user.id}>")

    @delink.error
    async def delink_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            if isinstance(error.original, discord.NotFound):
                await interaction.followup.send("The specified user does not exist or is not in the server", ephemeral=True)
            else:
                await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))


async def setup(client: commands.Bot):
    await client.add_cog(
        SlashLink(client), guild=discord.Object(id=os.getenv("GUILD_ID"))
    )
