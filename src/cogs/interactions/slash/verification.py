import os
import time
import discord
from discord import app_commands
from discord.ext import commands
import motor.motor_asyncio as motor
from utils import general as ug

mongo_client = motor.AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("DB_NAME")]
verified_collection = db["verified"]
batch_collection = db["batch"]


class SlashVerify(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="info", description="Get verification info about a user")
    @app_commands.describe(user="User to fetch info about")
    async def info(self, interaction: discord.Interaction, user: discord.Member):
        createdAt = user.created_at
        unixTimestamp = int(time.mktime(createdAt.timetuple()))
        joinedAt = user.joined_at
        unixJoinedTimestamp = int(time.mktime(joinedAt.timetuple())) if joinedAt else None
        
        geninfo = f"**Name:** {user.name}\n" \
               f"**ID:** {user.id}\n" \
               f"**Creation:** <t:{unixTimestamp}:R>\n"

        if unixJoinedTimestamp:
            geninfo += f"**Join:** <t:{unixJoinedTimestamp}:R>\n"

        embed = discord.Embed(title="User Info", description=geninfo, color=0x48BF91)
        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.response.send_message(embed=embed)
        if ug.has_mod_permissions(interaction.user):
            newEmbed = discord.Embed(title="Priviliged Info", color=0x48BF91)
            verRes = await verified_collection.find_one({"ID": str(user.id)})

            if not verRes:
                newEmbed.description = "This user is not verified yet"
                return await interaction.followup.send(embed=newEmbed, ephemeral=True)

            batchRes = await batch_collection.find_one({"PRN": verRes["PRN"]})

            if not batchRes:
                newEmbed.description = "Missing data!!!"
                return await interaction.followup.send(embed=newEmbed, ephemeral=True)
            
            newEmbed.description = f"**PRN:** {verRes['PRN']}"

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


    @app_commands.command(name="deverify", description="Remove a user's verification")
    @app_commands.describe(user="User to deverify")
    async def deverify(self, interaction: discord.Interaction, user: discord.Member):
        if not ug.has_mod_permissions(interaction.user):
            return await interaction.response.send_message("You are not authorised to run this command", ephemeral=True)

        await interaction.response.defer()
        result = await verified_collection.delete_one({"ID": str(user.id)})
        if result.deleted_count == 0:
            return await interaction.followup.send("This user was not verified in the first place", ephemeral=True)
        
        roles_to_remove = []
        for role in user.roles:
            if role.id != interaction.guild.id:
                roles_to_remove.append(role)
 
        try:
            await user.remove_roles(*roles_to_remove, reason="Deverification")

            just_joined_role = interaction.guild.get_role(ug.load_config_value("just_joined"))
            if just_joined_role:
                await user.add_roles(just_joined_role)
        except discord.Forbidden:
            return await interaction.followup.send("I am unable to remove roles from this user although they were deverified. Please check my permissions", ephemeral=True)

        await interaction.followup.send(f"De-verified <@{user.id}>")

    @deverify.error
    async def deverify_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            if isinstance(error.original, discord.NotFound):
                await interaction.followup.send("The specified user does not exist or is not in the server", ephemeral=True)
            else:
                await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))


async def setup(client: commands.Bot):
    await client.add_cog(
        SlashVerify(client), guild=discord.Object(id=os.getenv("GUILD_ID"))
    )
