import discord
from discord import app_commands
from discord.ext import commands
from pymongo import MongoClient
import json
import os


with open("config.json") as f:
    config = json.load(f)

mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client.get_database()
verified_collection = db["verified"]
batch_collection = db["batch"]


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Get verification info about a user.")
    @app_commands.describe(user="User to fetch info about")
    async def info(self, interaction: discord.Interaction, user: discord.Member):
        if not any(role.id in [config["admin"], config["mod"]] for role in interaction.user.roles):
            return await interaction.response.send_message("You are not authorised to run this command.", ephemeral=False)
        
        verRes = verified_collection.find_one({"ID": int(user.id)})

        if not verRes:
            return await interaction.response.send_message("This user is not verified yet.", ephemeral=True)

        batchRes = batch_collection.find_one({"PRN": verRes["PRN"]})

        if not batchRes:
            return await interaction.response.send_message("Missing data!!!", ephemeral=True)

        embed = discord.Embed(title="User Info", color=0x48BF91)
        embed.add_field(name="MemberID", value=verRes["ID"], inline=True)
        embed.add_field(name="PRN", value=batchRes["PRN"], inline=True)
        embed.add_field(name="Stream", value=batchRes["Branch"], inline=True)
        embed.add_field(name="Year", value=batchRes["Year"], inline=True)
        embed.add_field(name="Campus", value=batchRes["Campus"], inline=True)

        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="deverify", description="Remove a user's verification.")
    @app_commands.describe(user="User to deverify")
    async def deverify(self, interaction: discord.Interaction, user: discord.Member):
        if not any(role.id in [config["admin"], config["mod"]] for role in interaction.user.roles):
            return await interaction.response.send_message("You are not authorised to run this command.", ephemeral=False)

        result = verified_collection.delete_one({"ID": int(user.id)})
        if result.deleted_count == 0:
            return await interaction.response.send_message("This user was not verified in the first place.", ephemeral=True)
        
        roles_to_remove = []
        for role in user.roles:
            if role.id != interaction.guild.id:
                roles_to_remove.append(role)
 
        await user.remove_roles(*roles_to_remove, reason="Deverification")

        just_joined_role = interaction.guild.get_role(config["just_joined"])
        if just_joined_role:
            await user.add_roles(just_joined_role)

        await interaction.response.send_message(f"De-verified <@{user.id}>")

async def setup(bot: commands.Bot):
    await bot.add_cog(Verification(bot))
