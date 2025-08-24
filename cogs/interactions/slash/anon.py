import discord
import datetime
from bot import DiscordBot
from discord import app_commands
from discord.ext import commands, tasks
import utils.general as ug
from typing import Optional


class SlashAnon(commands.Cog):
    def __init__(self, client: DiscordBot):
        self.client = client
        self.anon_cache = {}
        self.ctx_menu = app_commands.ContextMenu(
            name="Ban this anon",
            callback=self.anon_ban_from_context_menu,
        )
        self.client.tree.add_command(self.ctx_menu)
        self.tasks = [self.check_anon_bans_loop, self.clear_anon_cache_loop]
        for task in self.tasks:
            if not task.is_running():
                task.start()

    async def cog_unload(self):
        for task in self.tasks:
            task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wait_until_ready()
        for task in self.tasks:
            if not task.is_running():
                task.start()

    def parse_time(self, time_str: str) -> int:
        time_str = time_str.lower().strip()
        try:
            if time_str.endswith("d"):
                return int(time_str[:-1]) * 24 * 60 * 60
            elif time_str.endswith("h"):
                return int(time_str[:-1]) * 60 * 60
            elif time_str.endswith("m"):
                return int(time_str[:-1]) * 60
            elif time_str.endswith("s"):
                return int(time_str[:-1])
            else:
                return int(time_str)
        except ValueError:
            raise ValueError("Invalid time format")

    @tasks.loop(seconds=30)
    async def check_anon_bans_loop(self):
        current_time = datetime.datetime.now(datetime.timezone.utc)
        async for ban in self.client.anonban_collection.find(
            {"expiresAt": {"$ne": None, "$lt": current_time}, "active": True}
        ):
            await self.client.anonban_collection.update_one(
                {"_id": ban["_id"]}, {"$set": {"active": False}}
            )
            user = await self.client.fetch_user(ban["userId"])
            if user:
                try:
                    embed = discord.Embed(
                        title="Notification",
                        description="Your anon messaging ban has expired",
                        color=discord.Color.green(),
                    )
                    embed.set_footer(text="PESU Bot")
                    embed.timestamp = discord.utils.utcnow()
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass

    @check_anon_bans_loop.before_loop
    async def before_check_anon_bans_loop(self):
        await self.client.wait_until_ready()

    @tasks.loop(hours=24)
    async def clear_anon_cache_loop(self):
        if self.anon_cache:
            self.anon_cache.clear()

    @clear_anon_cache_loop.before_loop
    async def before_clear_anon_cache_loop(self):
        await self.client.wait_until_ready()

    @app_commands.command(
        name="anon",
        description="Send messages anonymously to the general lobby channel",
    )
    @app_commands.describe(
        message="The message you want to send", link="Message link you want to reply to"
    )
    async def anon(
        self, interaction: discord.Interaction, message: str, link: Optional[str] = None
    ):
        await interaction.response.defer(ephemeral=True)
        userBanCheck = await self.client.anonban_collection.find_one(
            {"userId": str(interaction.user.id), "active": True}
        )
        if userBanCheck:
            return await interaction.followup.send(
                f":x: You have been banned from using anon messaging", ephemeral=True
            )

        if interaction.guild is None:
            return await interaction.followup.send(
                "This command can only be used in a server", ephemeral=True
            )
        lobbyChannelId = ug.load_channel_id("LOBBY")
        if not lobbyChannelId:
            return await interaction.followup.send(
                "Lobby channel not configured. Please contact the server admins.",
                ephemeral=True,
            )
        lobbyChannel = discord.utils.get(
            interaction.guild.channels, id=int(lobbyChannelId)
        )
        if not lobbyChannel:
            return await interaction.followup.send(
                "Lobby channel not found. Please contact the server admins.",
                ephemeral=True,
            )
        if not isinstance(lobbyChannel, discord.TextChannel):
            return await interaction.followup.send(
                "Lobby channel is not a text channel. Please contact the server admins.",
                ephemeral=True,
            )
        if not isinstance(interaction.user, discord.Member):
            return await interaction.followup.send(
                "This command can only be used by members of the server", ephemeral=True
            )
        perms = lobbyChannel.permissions_for(interaction.user)
        if not perms.send_messages:
            return await interaction.followup.send(
                "Looks like the channel is locked or you're muted. I won't send",
                ephemeral=True,
            )

        userLinkCheck = await self.client.link_collection.find_one(
            {"userId": str(interaction.user.id)}
        )
        if not userLinkCheck:
            return await interaction.followup.send(
                "You're not linked, so you can't use anon messaging. If this is a mistake, please contact Han",
                ephemeral=True,
            )

        # they passed the checks, so we can send the message

        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.followup.send(
                "The lobby channel is not a text channel. Please contact the server admins.",
                ephemeral=True,
            )
        if link is not None:
            try:
                reply_msg = await interaction.channel.fetch_message(
                    int(link.split("/")[-1])
                )
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                reply_msg = None
        else:
            reply_msg = None

        embed = discord.Embed(
            title="Anon Message", description=message, color=discord.Color.random()
        )

        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        embed.set_footer(text="PESU Bot")

        if reply_msg:
            anonMessage = await reply_msg.reply(embed=embed, mention_author=True)
            await interaction.followup.send(
                f":white_check_mark: Your anon message has been sent to <#{lobbyChannel.id}>"
            )
        else:
            anonMessage = await lobbyChannel.send(
                embed=embed, allowed_mentions=discord.AllowedMentions.none()
            )
            await interaction.followup.send(
                f":white_check_mark: Your anon message has been sent to <#{lobbyChannel.id}>"
            )

        if str(interaction.user.id) not in self.anon_cache:
            self.anon_cache[str(interaction.user.id)] = []

        self.anon_cache[str(interaction.user.id)].append(str(anonMessage.id))

    @anon.error
    async def anon_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(
        name="bananon", description="Ban a user from using anon based on message link"
    )
    @app_commands.describe(
        link="The message link you want to use to ban",
        time="Duration of the ban",
        reason="Reason for ban",
    )
    async def ban_anon(
        self,
        interaction: discord.Interaction,
        link: str,
        time: Optional[str] = None,
        reason: Optional[str] = "No reason provided",
    ):
        await interaction.response.defer(ephemeral=True)
        if not ug.has_mod_permissions(interaction.user):
            return await interaction.followup.send(
                "You ain't authorised to run this command", ephemeral=True
            )

        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.followup.send(
                "This command can only be used in a text channel", ephemeral=True
            )
        try:
            ban_msg = await interaction.channel.fetch_message(int(link.split("/")[-1]))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            ban_msg = None

        if not ban_msg:
            return await interaction.followup.send(
                "Could not find the message to ban from", ephemeral=True
            )

        if not interaction.guild:
            return await interaction.followup.send(
                "This command can only be used in a server", ephemeral=True
            )
        banUser = None
        for user_id, messages in self.anon_cache.items():
            if str(ban_msg.id) in messages:
                banUser = interaction.guild.get_member(int(user_id))
                break

        else:
            return await interaction.followup.send(
                "This wasn't an anon message only da what you doing?", ephemeral=True
            )

        if not banUser:
            return await interaction.followup.send(
                "Could not find the user to ban", ephemeral=True
            )

        userBanCheck = await self.client.anonban_collection.find_one(
            {"userId": str(banUser.id), "active": True}
        )
        if userBanCheck:
            return await interaction.followup.send(
                f"Dude's already banned from anon messaging", ephemeral=True
            )

        bannedAt = datetime.datetime.now(datetime.timezone.utc)
        if time is not None:
            try:
                seconds = self.parse_time(time)
                if seconds is None:
                    return await interaction.response.send_message(
                        "Mention the proper amount of time to be muted\nAccepted Time Format: Should end with `d/h/m/s`",
                        ephemeral=True,
                    )
            except ValueError:
                return await interaction.response.send_message(
                    "Mention the proper amount of time to be muted\nAccepted Time Format: Should end with `d/h/m/s`",
                    ephemeral=True,
                )

            if seconds <= 10:
                return await interaction.followup.send(
                    "You can't ban someone for less than 10 seconds", ephemeral=True
                )
            expiresAt = bannedAt + datetime.timedelta(seconds=seconds)
        else:
            expiresAt = None
        ban_data = {
            "userId": str(banUser.id),
            "reason": reason,
            "bannedAt": bannedAt,
            "expiresAt": expiresAt,
            "active": True,
        }
        await self.client.anonban_collection.insert_one(ban_data)
        bantimestamp = "Permanent" if expiresAt is None else f"<t:{int(expiresAt.timestamp())}:R>"
        if bantimestamp == "Permanent":
            await interaction.followup.send(
                f"Member has been banned from anon messaging, their ban will never expire\nReason: {reason}"
            )
        else:
            await interaction.followup.send(
                f"Member has been banned from anon messaging, their ban will expire {bantimestamp}\nReason: {reason}"
            )

        try:
            banEmbed = discord.Embed(
                title="Notification",
                description="You have been banned from using anon messaging",
                color=discord.Color.red(),
            )
            banEmbed.add_field(
                name="Reason",
                value=reason if reason else "No reason provided",
                inline=False,
            )
            banEmbed.add_field(
                name="Message Link",
                value=f"[Click here to view the message]({link})",
                inline=False,
            )
            banEmbed.add_field(
                name="Expires",
                value= bantimestamp,
                inline=False,
            )
            banEmbed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            banEmbed.set_footer(text="PESU Bot")
            await banUser.send(embed=banEmbed)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send("DMs were closed", ephemeral=True)

    @ban_anon.error
    async def ban_anon_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    async def anon_ban_from_context_menu(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        await interaction.response.defer(ephemeral=True)
        if ug.has_mod_permissions(interaction.user):
            ban_msg = message
            banUser = None
            if not isinstance(interaction.guild, discord.Guild):
                return await interaction.followup.send(
                    "This command can only be used in a server", ephemeral=True
                )
            if not isinstance(interaction.channel, discord.TextChannel):
                return await interaction.followup.send(
                    "This command can only be used in a text channel", ephemeral=True
                )
            for user_id, messages in self.anon_cache.items():
                if str(ban_msg.id) in messages:
                    banUser = interaction.guild.get_member(int(user_id))
                    break
            else:
                return await interaction.followup.send(
                    "This wasn't an anon message only da what you doing?",
                    ephemeral=True,
                )

            if not banUser:
                return await interaction.followup.send(
                    "Could not find the user to ban", ephemeral=True
                )

            userBanCheck = await self.client.anonban_collection.find_one(
                {"userId": str(banUser.id), "active": True}
            )
            if userBanCheck:
                return await interaction.followup.send(
                    f"Dude's already banned from anon messaging", ephemeral=True
                )

            bannedAt = datetime.datetime.now(datetime.timezone.utc)
            defaultExpiry = None
            await self.client.anonban_collection.insert_one(
                {
                    "userId": str(banUser.id),
                    "reason": "No reason provided, executed via context menu",
                    "bannedAt": bannedAt,
                    # set default ban time as infinite
                    "expiresAt": defaultExpiry,
                    "active": True,
                }
            )

            try:
                embed = discord.Embed(
                    title="Notification",
                    description="You have been banned from using anon messaging",
                    color=discord.Color.red(),
                )
                embed.add_field(
                    name="Reason",
                    value="No reason provided, executed via context menu",
                    inline=False,
                )
                embed.add_field(
                    name="Message Link",
                    value=f"[Jump to message](https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message.id})",
                    inline=False,
                )
                embed.add_field(
                    name="Expires",
                    value="Permanent",
                    inline=False,
                )
                embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
                embed.set_footer(text="PESU Bot")
                await banUser.send(embed=embed)
                await interaction.followup.send(
                    f"Member has been banned from anon messaging, their ban will never expire:R>\nReason:  No reason provided, executed via context menu",
                    ephemeral=True,
                )
            except (discord.Forbidden, discord.HTTPException):
                await interaction.followup.send(
                    f"Member has been banned from anon messaging, their ban will never expire but I couldn't DM them\nReason: No reason provided, executed via context menu",
                    ephemeral=True,
                )
        else:
            return await interaction.followup.send(
                "You are not authorised to use this", ephemeral=True
            )

    @app_commands.command(
        name="userbananon", description="Manually ban a user from anon messaging"
    )
    @app_commands.describe(
        member="The member to ban", time="Duration of the ban", reason="Reason for ban"
    )
    async def user_ban_anon(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        time: Optional[str] = None,
        reason: Optional[str] = "No reason provided",
    ):
        await interaction.response.defer(ephemeral=True)

        if not ug.has_mod_permissions(interaction.user):
            return await interaction.followup.send(
                "You ain't authorised to run this command", ephemeral=True
            )

        userBanCheck = await self.client.anonban_collection.find_one(
            {"userId": str(member.id), "active": True}
        )
        if userBanCheck:
            return await interaction.followup.send(
                "Dude's already banned from anon messaging", ephemeral=True
            )

        if time is not None:
            try:
                seconds = self.parse_time(time)
            except ValueError:
                return await interaction.followup.send(
                    "Invalid time format. Please use a valid time format.", ephemeral=True
                )

            if seconds <= 10:
                return await interaction.followup.send(
                    "You can't ban someone for less than 10 seconds", ephemeral=True
                )
        else:
            seconds = None

        bannedAt = datetime.datetime.now(datetime.timezone.utc)
        if time is not None:
            try:
                seconds = self.parse_time(time)
                if seconds is None:
                    return await interaction.response.send_message(
                        "Mention the proper amount of time to be muted\nAccepted Time Format: Should end with `d/h/m/s`",
                        ephemeral=True,
                    )
            except ValueError:
                return await interaction.response.send_message(
                    "Mention the proper amount of time to be muted\nAccepted Time Format: Should end with `d/h/m/s`",
                    ephemeral=True,
                )

            if seconds <= 10:
                return await interaction.followup.send(
                    "You can't ban someone for less than 10 seconds", ephemeral=True
                )
            expiresAt = bannedAt + datetime.timedelta(seconds=seconds)
        else:
            expiresAt = None

        
            

        ban_data = {
            "userId": str(member.id),
            "reason": reason,
            "bannedAt": bannedAt,
            "expiresAt": expiresAt,
            "active": True,
        }
        await self.client.anonban_collection.insert_one(ban_data)
        bantimestamp = "Permanent" if expiresAt is None else f"<t:{int(expiresAt.timestamp())}:R>"
        if bantimestamp == "Permanent":
            await interaction.followup.send(
                f"Member has been banned from anon messaging, their ban will never expire\nReason: {reason}"
            )
        else:
            await interaction.followup.send(
                f"Member has been banned from anon messaging, their ban will expire {bantimestamp}\nReason: {reason}"
            )

        try:
            banEmbed = discord.Embed(
                title="Notification",
                description="You have been banned from using anon messaging",
                color=discord.Color.red(),
            )
            banEmbed.add_field(name="Reason", value=reason)
            banEmbed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            banEmbed.add_field(
                name="Expires", value=bantimestamp, inline=False
            )
            banEmbed.set_footer(text="PESU Bot")
            await member.send(embed=banEmbed)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send("DMs were closed", ephemeral=True)

    @user_ban_anon.error
    async def user_ban_anon_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(
        name="userunbananon", description="Unban a user from anon messaging"
    )
    @app_commands.describe(member="The member to unban")
    async def user_unban_anon(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        await interaction.response.defer(ephemeral=True)

        if not ug.has_mod_permissions(interaction.user):
            return await interaction.followup.send(
                "You ain't authorised to run this command", ephemeral=True
            )

        # result = await self.anonban_collection.find_one_and_delete({"userId": str(member.id)})
        # set active to false instead of deleting the document
        result = await self.client.anonban_collection.find_one_and_update(
            {"userId": str(member.id), "active": True}, {"$set": {"active": False}}
        )
        if result is None:
            return await interaction.followup.send(
                "This fellow wasn't even anon-banned in the first place", ephemeral=True
            )

        await interaction.followup.send("Member unbanned successfully")

        try:
            unbanEmbed = discord.Embed(
                title="Notification",
                description="Your anon messaging ban has been revoked",
                color=discord.Color.green(),
            )
            unbanEmbed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            unbanEmbed.set_footer(text="PESU Bot")
            await member.send(embed=unbanEmbed)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send("DMs were closed", ephemeral=True)

    @user_unban_anon.error
    async def user_unban_anon_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(
        name="anonbaninfo", description="Get info about a user's anon ban"
    )
    @app_commands.describe(member="The member to get info about")
    async def anon_ban_info(
        self, interaction: discord.Interaction, member: discord.Member
    ):
        await interaction.response.defer(ephemeral=True)

        if not ug.has_mod_permissions(interaction.user):
            return await interaction.followup.send(
                "You ain't authorised to run this command", ephemeral=True
            )

        userBanCheck = await self.client.anonban_collection.find_one(
            {"userId": str(member.id), "active": True}
        )
        if not userBanCheck:
            return await interaction.followup.send(
                "This fellow is not banned from anon messaging", ephemeral=True
            )

        bannedAt = userBanCheck["bannedAt"]
        expiresAt = userBanCheck["expiresAt"]
        expiryTimestamp = f"<t:{int(expiresAt.timestamp())}:R>" if expiresAt else "Permanent"

        embed = discord.Embed(title="Anon Ban Info", color=discord.Color.red())
        embed.add_field(name="User", value=member.mention, inline=False)
        embed.add_field(
            name="Reason",
            value=userBanCheck.get("reason", "No reason provided"),
            inline=False,
        )
        embed.add_field(
            name="Banned", value=f"<t:{int(bannedAt.timestamp())}:R>", inline=False
        )
        embed.add_field(
            name="Expires", value=expiryTimestamp, inline=False
        )
        embed.set_footer(text="PESU Bot")
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

        await interaction.followup.send(embed=embed)


async def setup(client: DiscordBot):
    cog = SlashAnon(client)
    await client.add_cog(
        cog, guild=discord.Object(id=ug.load_config_value("GUILD", {}).get("ID"))
    )
    client.tree.add_command(
        cog.ctx_menu,
        guild=discord.Object(id=ug.load_config_value("GUILD", {}).get("ID")),
    )
