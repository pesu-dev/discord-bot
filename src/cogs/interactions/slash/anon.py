import os
import discord
import datetime
from discord import app_commands
from discord.ext import commands
import motor.motor_asyncio as motor
from utils import general as ug
from typing import Optional

mongo_client = motor.AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("DB_NAME")]
verified_collection = db["verified"]
batch_collection = db["batch"]
anonbans_collection = db["anonbans"]



class SlashAnon(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.anon_cache = {}
        self.ctx_menu = app_commands.ContextMenu(
            name='Ban this anon',
            callback=self.anon_ban_from_context_menu,
        )
        self.client.tree.add_command(self.ctx_menu)


    @app_commands.command(name="anon", description="Send messages anonymously to the general lobby channel")
    @app_commands.describe(message="The message you want to send", link="Message link you want to reply to")
    async def anon(self, interaction: discord.Interaction, message: str, link: Optional[str] = None):
        await interaction.response.defer(ephemeral=True)
        userBanCheck = await anonbans_collection.find_one({"ID": str(interaction.user.id)})
        if userBanCheck:
            return await interaction.followup.send(":x: You have been banned from using anon messaging", ephemeral=True)

        lobbyChannel = discord.utils.get(interaction.guild.channels, id=int(ug.load_config_value("lobbyChannel")))
        perms = lobbyChannel.permissions_for(interaction.user)
        if not perms.send_messages:
            return await interaction.followup.send("Looks like the channel is locked or you're muted. I won't send", ephemeral=True)
        
        
        userVerifyCheck = await verified_collection.find_one({"ID": str(interaction.user.id)})
        if not userVerifyCheck:
            return await interaction.followup.send("You're not verified, so you can't use anon messaging. If this is a mistake, please contact Han", ephemeral=True)
        
        # they passed the checks, so we can send the message

        if link is not None:
            try:
                reply_msg = await interaction.channel.fetch_message(link.split("/")[-1])
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                reply_msg = None
        else:
            reply_msg = None

        embed = discord.Embed(
            title="Anon Message",
            description=message,
            color=discord.Color.blurple()
        )
        
        ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        embed.timestamp = datetime.datetime.now(ist)

        if reply_msg:
            anonMessage = await reply_msg.reply(embed=embed, mention_author=True)
            await interaction.followup.send(f":white_check_mark: Your anon message has been sent to <#{lobbyChannel.id}>")
        else:
            anonMessage = await lobbyChannel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none()
            )
            await interaction.followup.send(f":white_check_mark: Your anon message has been sent to <#{lobbyChannel.id}>")

        if str(interaction.user.id) not in self.anon_cache:
            self.anon_cache[str(interaction.user.id)] = []

        self.anon_cache[str(interaction.user.id)].append(str(anonMessage.id))

    @anon.error
    async def anon_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

        

    @app_commands.command(name="bananon", description="Ban a user from using anon based on message link")
    @app_commands.describe(link="The message link you want to use to ban",  reason="Reason for ban")
    async def ban_anon(self, interaction: discord.Interaction, link: str, reason: Optional[str] = "No reason provided"):
        await interaction.response.defer(ephemeral=True)
        if not ug.has_mod_permissions(interaction.user):
            return await interaction.followup.send("You ain't authorised to run this command", ephemeral=True)
        
        try:
            ban_msg = await interaction.channel.fetch_message(link.split("/")[-1])
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            ban_msg = None

        if not ban_msg:
            return await interaction.followup.send("Could not find the message to ban from", ephemeral=True)
        
        banUser = None
        for user_id, messages in self.anon_cache.items():
            if str(ban_msg.id) in messages:
                banUser = interaction.guild.get_member(int(user_id))
                break
                
        else:
            return await interaction.followup.send("This wasn't an anon message only da what you doing?", ephemeral=True)

        if not banUser:
            return await interaction.followup.send("Could not find the user to ban", ephemeral=True)
        

        userBanCheck = await anonbans_collection.find_one({"ID": str(banUser.id)})
        if userBanCheck:
            return await interaction.followup.send(f"Dude's already banned from anon messaging", ephemeral=True)
        
        ban_data = {
            "ID": str(banUser.id),
            "Reason": reason if reason else "No reason provided",
        }
        await anonbans_collection.insert_one(ban_data)

        await interaction.followup.send(f"Member has been banned from anon messaging\nReason: {reason}")

        try:
            banEmbed = discord.Embed(
                title="Notification",
                description="You have been banned from using anon messaging",
                color=discord.Color.red()
            )
            banEmbed.add_field(name="Reason", value=reason if reason else "No reason provided", inline=False)
            banEmbed.add_field(name="Message Link", value=f"[Click here to view the message]({link})", inline=False)
            ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
            banEmbed.timestamp = datetime.datetime.now(ist)
            await banUser.send(embed=banEmbed)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send("DMs were closed", ephemeral=True)

    @ban_anon.error
    async def ban_anon_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    async def anon_ban_from_context_menu(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(ephemeral=True)
        if ug.has_mod_permissions(interaction.user):
            ban_msg = message
            banUser = None
            for user_id, messages in self.anon_cache.items():
                if str(ban_msg.id) in messages:
                    banUser = interaction.guild.get_member(int(user_id))
                    break
            else:
                return await interaction.followup.send("This wasn't an anon message only da what you doing?", ephemeral=True)

            if not banUser:
                return await interaction.followup.send("Could not find the user to ban", ephemeral=True)

            userBanCheck = await anonbans_collection.find_one({"ID": str(banUser.id)})
            if userBanCheck:
                return await interaction.followup.send(f"Dude's already banned from anon messaging", ephemeral=True)
            await anonbans_collection.insert_one({
                "ID": str(banUser.id),
                "Reason": "No reason provided, executed via context menu"
            })

            try:
                embed = discord.Embed(
                    title="Notification",
                    description="You have been banned from using anon messaging",
                    color=discord.Color.red()
                )
                embed.add_field(name="Reason", value="No reason provided, executed via context menu", inline=False)
                embed.add_field(name="Message Link", value=f"[Jump to message](https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message.id})", inline=False)
                ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
                embed.timestamp = datetime.datetime.now(ist)
                await banUser.send(embed=embed)
                await interaction.followup.send(f"Member has been banned from anon messaging\nReason:  No reason provided, executed via context menu", ephemeral=True)
            except (discord.Forbidden, discord.HTTPException):
                await interaction.followup.send("Member has been banned from anon messaging, but I couldn't DM them\nReason: No reason provided, executed via context menu", ephemeral=True)
        else:
            return await interaction.followup.send("You are not authorised to use this", ephemeral=True)

    @app_commands.command(name="userbananon", description="Manually ban a user from anon messaging")
    @app_commands.describe(member="The member to ban", reason="Reason for ban")
    async def user_ban_anon(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "No reason specified"):
        await interaction.response.defer(ephemeral=True)

        if not ug.has_mod_permissions(interaction.user):
            return await interaction.followup.send("You ain't authorised to run this command", ephemeral=True)

        userBanCheck = await anonbans_collection.find_one({"ID": str(member.id)})
        if userBanCheck:
            return await interaction.followup.send("Dude's already banned from anon messaging", ephemeral=True)

        ban_data = {
            "ID": str(member.id),
            "Reason": reason
        }
        await anonbans_collection.insert_one(ban_data)
        await interaction.followup.send(f"Member has been banned from anon messaging\nReason: {reason}")

        try:
            banEmbed = discord.Embed(
                title="Notification",
                description="You have been banned from using anon messaging",
                color=discord.Color.red()
            )
            banEmbed.add_field(name="Reason", value=reason)
            ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
            banEmbed.timestamp = datetime.datetime.now(ist)
            await member.send(embed=banEmbed)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send("DMs were closed", ephemeral=True)

    @user_ban_anon.error
    async def user_ban_anon_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(name="userunbananon", description="Unban a user from anon messaging")
    @app_commands.describe(member="The member to unban")
    async def user_unban_anon(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)

        if not ug.has_mod_permissions(interaction.user):
            return await interaction.followup.send("You ain't authorised to run this command", ephemeral=True)

        result = await anonbans_collection.find_one_and_delete({"ID": str(member.id)})

        if result is None:
            return await interaction.followup.send("This fellow wasn't even anon-banned in the first place", ephemeral=True)

        await interaction.followup.send("Member unbanned successfully")

        try:
            unbanEmbed = discord.Embed(
                title="Notification",
                description="Your anon messaging ban has been revoked",
                color=discord.Color.green()
            )
            ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
            unbanEmbed.timestamp = datetime.datetime.now(ist)
            await member.send(embed=unbanEmbed)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send("DMs were closed", ephemeral=True)

    @user_unban_anon.error
    async def user_unban_anon_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
    



async def setup(client: commands.Bot):
    cog = SlashAnon(client)
    await client.add_cog(cog, guild=discord.Object(id=os.getenv("GUILD_ID")))
    client.tree.add_command(cog.ctx_menu, guild=discord.Object(id=os.getenv("GUILD_ID")))