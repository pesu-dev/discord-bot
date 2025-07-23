import discord
import datetime as dt
from typing import Optional
from bot import DiscordBot
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from discord.utils import utcnow
import utils.general as ug


class SlashMod(commands.Cog):
    def __init__(self, client: DiscordBot):
        self.client = client
        self.tasks = [self.check_mutes_loop]
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
    async def check_mutes_loop(self):
        now = datetime.now(dt.timezone.utc)
        expired_mutes = await self.client.mute_collection.find(
            {"unmute_time": {"$lte": now}, "active": True}
        ).to_list(length=100)

        config_guildid = ug.load_config_value("GUILD", {}).get("ID")
        guild = self.client.get_guild(config_guildid)
        for mute in expired_mutes:         
            if not guild:
                try:
                    guild = await self.client.fetch_guild(config_guildid)
                except discord.NotFound:
                    print(f"I couldn't find guild with ID {config_guildid}")
                    continue
                except discord.Forbidden:
                    print(f"I don't have permissions to fetch guild {config_guildid}")
                    continue

            try:
                member = await guild.fetch_member(mute["user_id"])
            except discord.NotFound:
                await self.client.mute_collection.update_one(
                    {"_id": mute["_id"]},
                    {
                        "$set": {
                            "active": False,
                            "unmute_time": now,
                            "unmute_type": "auto_member_left",
                        }
                    },
                )
                continue

            muted_role_id = ug.load_role_id("MUTED")
            if not muted_role_id:
                continue
            muted_role = discord.utils.get(guild.roles, id=int(muted_role_id))
            if muted_role and muted_role in member.roles:
                try:
                    await member.remove_roles(muted_role, reason="Automatic unmute by loop")
                except discord.Forbidden:
                    print(f"PERMISSION ERROR: Bot cannot remove role in '{guild.name}'. Check Role Hierarchy and 'Manage Roles' permission.")
                    continue
                except discord.HTTPException as e:
                    print(f"HTTP ERROR while removing role: {e}")
                    continue

            await self.client.mute_collection.update_one(
                {"_id": mute["_id"]},
                {
                    "$set": {
                        "active": False,
                        "unmute_time": now,
                        "unmute_type": "loop_auto",
                    }
                },
            )

            channel = guild.get_channel(mute["channel_id"])
            if not isinstance(channel, discord.TextChannel):
                continue
            if channel:
                unmute_embed = discord.Embed(
                    title="Unmute", color=discord.Color.green(), timestamp=now
                )
                unmute_embed.add_field(
                    name="Unmuted user",
                    value=f"{member.mention} welcome back",
                    inline=False,
                )
                unmute_embed.set_footer(text="PESU Bot")
                try:
                    await channel.send(content=f"{member.mention}", embed=unmute_embed)
                except discord.HTTPException:
                    pass

            mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
            if not mod_logs_id:
                continue
            mod_logs = guild.get_channel(int(mod_logs_id))
            if not isinstance(mod_logs, discord.TextChannel):
                continue
            if mod_logs:
                unmute_logs_embed = discord.Embed(
                    title="Unmute", color=discord.Color.green(), timestamp=now
                )

                unmute_logs_embed.add_field(
                    name="Unmuted user",
                    value=f"{member.mention}\nModerator: Auto",
                    inline=False,
                )
                unmute_logs_embed.set_footer(text="PESU Bot")

                try:
                    await mod_logs.send(embed=unmute_logs_embed)
                except discord.HTTPException:
                    pass

    @check_mutes_loop.before_loop
    async def before_check_mutes_loop(self):
        await self.client.wait_until_ready()

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided",
    ):
        if not ug.has_mod_permissions(interaction.user):
            await interaction.response.send_message(
                "Noob you can't do that", ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                "You dare kick one of my brothers you little twat", ephemeral=True
            )
            return

        if member is None:
            await interaction.response.send_message("Please mention someone to kick")
            return

        if ug.has_mod_permissions(member):
            await interaction.response.send_message("Gomma you can't kick admin/mod")
            return

        try:
            if not interaction.guild:
                return await interaction.response.send_message(
                    "This command can only be used in a server", ephemeral=True
                )
            await member.send(
                f"You have been kicked from **{interaction.guild.name}**\nReason: {reason}"
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

        await member.kick(reason=f"Kicked by {interaction.user} | {reason}")
        embed = discord.Embed(
            title="Member Kicked",
            color=discord.Color.red(),
            description=f"{member.mention} was kicked by {interaction.user.mention}\n**Reason:** {reason}",
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text="PESU Bot")
        await interaction.response.send_message(embed=embed)
        mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mod_logs_id:
            return
        mod_logs_channel = self.client.get_channel(int(mod_logs_id))
        if not isinstance(mod_logs_channel, discord.TextChannel):
            return
        if mod_logs_channel:
            await mod_logs_channel.send(embed=embed)
        else:
            print(
                f"Mod logs channel not found: {ug.load_channel_id('MOD_LOGS', logs=True)}"
            )

    @app_commands.command(
        name="echo", description="Echoes a message to the target channel"
    )
    @app_commands.describe(
        channel="The channel to send the message to",
        message="The message to send",
        attachment="An optional attachment to send with the message",
    )
    async def echo(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: str,
        attachment: Optional[discord.Attachment] = None,
    ):
        await interaction.response.defer(ephemeral=True)
        if not ug.has_mod_permissions(
            interaction.user
        ) and not ug.has_bot_dev_permissions(interaction.user):
            return await interaction.response.send_message(
                "You are not authorised to run this command", ephemeral=True
            )
        if not attachment:
            await channel.send(message)
        else:
            await channel.send(message, file=await attachment.to_file())
        await interaction.followup.send(f"Message sent to {channel.mention}")
        if not interaction.guild:
            return
        mods_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mods_logs_id:
            return
        mods_logs = interaction.guild.get_channel(mods_logs_id)
        if not isinstance(mods_logs, discord.TextChannel):
            return
        if mods_logs:
            echo_embed = discord.Embed(
                title="Echo Sent",
                #description=f"Message: {message}\nChannel: {channel.mention}\nAttachment: {'Yes' if attachment else 'No'}\nAuthor: {interaction.user.mention}",
                color=discord.Color.blue(),
                timestamp=datetime.now(dt.timezone.utc),
            )
            echo_embed.add_field(
                name="Message",
                value=message,
                inline=False
            )
            echo_embed.add_field(
                name="Channel",
                value=channel.mention,
                inline=False
            )
            echo_embed.add_field(
                name="Attachment",
                value="Yes" if attachment else "No",
                inline=False
            )
            echo_embed.add_field(
                name="Author",
                value=interaction.user.mention,
                inline=False
            )
            echo_embed.set_footer(text=f"PESU Bot")
            await mods_logs.send(embed=echo_embed)

    @echo.error
    async def echo_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            if isinstance(error.original, discord.Forbidden):
                await interaction.followup.send(
                    "I do not have permission to send messages in that channel",
                    ephemeral=True,
                )
            elif isinstance(error.original, discord.NotFound):
                await interaction.followup.send(
                    "The specified channel does not exist", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error.original)
                )
        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(
        name="changenick", description="Change someone else's nickname"
    )
    @app_commands.describe(
        member="The member whose name you want to change",
        new_nick="The new nickname you wanna give this user",
    )
    async def changenick(
        self, interaction: discord.Interaction, member: discord.Member, new_nick: str
    ):
        await interaction.response.defer(ephemeral=True)
        if not ug.has_mod_permissions(interaction.user):
            return await interaction.followup.send(
                f"Awwww sooo cutely you're trying to change {member.display_name}'s nickname",
                ephemeral=True,
            )
        newNick = new_nick.strip()
        await member.edit(nick=newNick)
        await interaction.followup.send(
            f"Nicely changed {member.display_name}'s name to {newNick}", ephemeral=True
        )

    @changenick.error
    async def changenick_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This user doesn't even exist here, who are you trying to change the name of?",
                    ephemeral=True,
                )

            elif isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to change this user's nickname at this time",
                    ephemeral=True,
                )

            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @kick.error
    async def kick_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This user doesn't even exist here, who are you trying to kick?",
                    ephemeral=True,
                )

            elif isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to kick this user at this time", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(
        name="mute", description="Mute a member for a specified duration"
    )
    @app_commands.describe(
        member="The member to mute (or yourself for self-mute)",
        time="Duration for mute (e.g., 1h, 30m, 2d)",
        reason="Reason for the mute",
    )
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        time: str,
        reason: str = "No reason provided",
    ):
        if not interaction.guild:
            return await interaction.response.send_message(
                "This command can only be used in a server", ephemeral=True
            )
        muted_role_id = ug.load_role_id("MUTED")
        if not muted_role_id:
            return await interaction.response.send_message(
                "Muted role is not configured in the bot", ephemeral=True
            )
        muted_role = discord.utils.get(interaction.guild.roles, id=int(muted_role_id))
        if not muted_role:
            return await interaction.response.send_message(
                "Muted role is not found in the server", ephemeral=True
            )
        if interaction.user.id == member.id:
            is_self_mute = True
        else:
            if not ug.has_mod_permissions(interaction.user):
                await interaction.response.send_message(
                    "You are not authorised to do that", ephemeral=True
                )
                return
            is_self_mute = False

        try:
            seconds = self.parse_time(time)
        except ValueError:
            await interaction.response.send_message(
                "Mention the proper amount of time to be muted\nAccepted Time Format: Should end with `d/h/m/s`",
                ephemeral=True,
            )
            return

        if seconds <= 0 or seconds > 1209600:
            await interaction.response.send_message(
                "Mute time limit is 14 days only", ephemeral=True
            )
            return

        if is_self_mute and seconds < 3600:
            await interaction.response.send_message(
                "Self-mute is only for 1 hour or more", ephemeral=True
            )
            return

        if muted_role in member.roles:
            await interaction.response.send_message(
                "Brother, leave the already muted poor soul alone", ephemeral=True
            )
            return

        if not is_self_mute and ug.has_mod_permissions(member):
            await interaction.response.send_message(
                "Leyy, he's admin/mod. Can't mute them", ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                "You dare mute one of my kind nin amn", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)

        await member.add_roles(muted_role)
        mute_time = datetime.now(dt.timezone.utc)
        unmute_time = mute_time + timedelta(seconds=seconds)

        if not interaction.channel:
            return await interaction.response.send_message(
                "This command can only be used in a server", ephemeral=True
            )

        mute_record = {
            "user_id": member.id,
            "channel_id": interaction.channel.id,
            "moderator_id": interaction.user.id,
            "mute_time": mute_time,
            "unmute_time": unmute_time,
            "reason": reason,
            "active": True,
            "is_self_mute": is_self_mute,
        }
        await self.client.mute_collection.insert_one(mute_record)

        mute_embed = discord.Embed(
            title="Mute",
            color=discord.Color.red(),
            timestamp=datetime.now(dt.timezone.utc),
        )
        unmute_timestamp = int(unmute_time.timestamp())
        mute_embed.add_field(
            name="Muted User",
            value=f"{member.mention} was muted\nUnmute: <t:{unmute_timestamp}:R>\nReason: {reason}",
            inline=False,
        )
        mute_embed.set_footer(text="PESU Bot")
        await interaction.followup.send(embed=mute_embed)

        mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mod_logs_id:
            return
        mod_logs = interaction.guild.get_channel(int(mod_logs_id))
        if not isinstance(mod_logs, discord.TextChannel):
            return
        if mod_logs:
            mute_logs_embed = discord.Embed(
                title="Mute",
                color=discord.Color.red(),
                timestamp=datetime.now(dt.timezone.utc),
            )
            moderator_mention = (
                f"<@{interaction.user.id}>" if not is_self_mute else "Self"
            )
            mute_logs_embed.add_field(
                name="Muted User",
                value=f"{member.mention}\nTime: {time}\nReason: {reason}\nModerator: {moderator_mention}",
                inline=False,
            )
            mute_logs_embed.set_footer(text="PESU Bot")
            await mod_logs.send(embed=mute_logs_embed)

    @mute.error
    async def mute_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This user doesn't even exist here, who are you trying to mute?",
                    ephemeral=True,
                )

            elif isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to mute this user at this time", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(name="unmute", description="Unmute a member")
    @app_commands.describe(member="The member to unmute")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not ug.has_mod_permissions(interaction.user):
            await interaction.response.send_message(
                "You are not authorised to do this", ephemeral=True
            )
            return

        if not interaction.guild:
            return await interaction.response.send_message(
                "This command can only be used in a server", ephemeral=True
            )
        muted_role_id = ug.load_role_id("MUTED")
        if not muted_role_id:
            return await interaction.response.send_message(
                "Muted role is not configured in the bot", ephemeral=True
            )
        muted_role = discord.utils.get(interaction.guild.roles, id=int(muted_role_id))
        if not muted_role:
            return await interaction.response.send_message(
                "Muted role is not found in the server", ephemeral=True
            )

        if muted_role not in member.roles:
            await interaction.response.send_message(
                "Why you trynna unmute someone who ain't muted?", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)

        await member.remove_roles(muted_role)

        await self.client.mute_collection.update_many(
            {"user_id": member.id, "guild_id": interaction.guild.id, "active": True},
            {
                "$set": {
                    "active": False,
                    "unmute_time": datetime.now(dt.timezone.utc),
                    "unmute_type": "manual",
                    "unmuted_by": interaction.user.id,
                }
            },
        )

        unmute_embed = discord.Embed(
            title="Unmute",
            color=discord.Color.green(),
            timestamp=datetime.now(dt.timezone.utc),
        )
        unmute_embed.set_footer(text="PESU Bot")
        unmute_embed.add_field(
            name="Unmuted user", value=f"{member.mention} welcome back", inline=False
        )

        await interaction.followup.send(embed=unmute_embed)

        mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mod_logs_id:
            return
        mod_logs = interaction.guild.get_channel(int(mod_logs_id))
        if not isinstance(mod_logs, discord.TextChannel):
            return
        if mod_logs:
            unmute_logs_embed = discord.Embed(
                title="Unmute",
                color=discord.Color.green(),
                timestamp=datetime.now(dt.timezone.utc),
            )
            unmute_logs_embed.set_footer(text="PESU Bot")
            unmute_logs_embed.add_field(
                name="Unmuted user",
                value=f"{member.mention}\nModerator: {interaction.user.mention}",
                inline=False,
            )
            await mod_logs.send(embed=unmute_logs_embed)

    @unmute.error
    async def unmute_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This user doesn't even exist here, who are you trying to unmute?",
                    ephemeral=True,
                )

            elif isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to unmute this user at this time", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(
        name="purge", description="Delete a number of recent messages"
    )
    @app_commands.describe(amount="Number of messages to delete")
    async def purge(self, interaction: discord.Interaction, amount: int):

        if not interaction.channel:
            return await interaction.response.send_message(
                "This command can only be used in a server", ephemeral=True
            )
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message(
                "This command can only be used in a text channel", ephemeral=True
            )
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "This command can only be used by members", ephemeral=True
            )
        if not interaction.channel.permissions_for(interaction.user).manage_messages:
            await interaction.response.send_message(
                "You don't have permission to delete messages", ephemeral=True
            )
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "Please specify a number between 1 and 100", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Deleted last {len(deleted)} messages")
        embed = discord.Embed(
            title="Messages Purged",
            color=discord.Color.green(),
            description=f"{len(deleted)} messages were deleted in {interaction.channel.mention} by {interaction.user.mention}",
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text="PESU Bot")
        mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mod_logs_id:
            return
        mod_logs_channel = self.client.get_channel(int(mod_logs_id))
        if not isinstance(mod_logs_channel, discord.TextChannel):
            return
        if mod_logs_channel:
            await mod_logs_channel.send(embed=embed)
        else:
            print(
                f"Mod logs channel not found: {ug.load_channel_id('MOD_LOGS', logs=True)}"
            )

    @purge.error
    async def purge_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to delete messages in this channel at this time",
                    ephemeral=True,
                )
            elif isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This channel doesn't exist or has been deleted", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(name="lock", description="lock a channel")
    @app_commands.describe(
        channel="The channel to lock (defaults to current channel)",
        reason="Reason for locking the channel",
    )
    async def lock_channel(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
        reason: str = "No reason provided",
    ):
        if not ug.has_mod_permissions(interaction.user):
            await interaction.response.send_message(
                "I am not dyno to let you do this", ephemeral=True
            )
            return

        if channel is None:
            if not isinstance(interaction.channel, discord.TextChannel):
                return await interaction.response.send_message(
                    "This command can only be used in a text channel", ephemeral=True
                )
            channel = interaction.channel

        if not interaction.guild:
            return await interaction.response.send_message(
                "This command can only be used in a server", ephemeral=True
            )
        everyone_role = interaction.guild.default_role

        overwrites = channel.overwrites_for(everyone_role)
        if overwrites.send_messages is False:
            await interaction.response.send_message(
                "This channel is already locked", ephemeral=True
            )
            return

        overwrites.send_messages = False
        await channel.set_permissions(everyone_role, overwrite=overwrites)
        await interaction.response.send_message(
            f"Locked {channel.mention}", ephemeral=False
        )

        lock_embed = discord.Embed(
            title="Channel Locked :lock:",
            color=discord.Color.red(),
            description=reason,
            timestamp=datetime.now(dt.timezone.utc),
        )
        lock_embed.set_footer(text="PESU Bot")
        await channel.send(embed=lock_embed)

        lock_logs_embed = discord.Embed(
            title="Lock",
            color=discord.Color.red(),
            timestamp=datetime.now(dt.timezone.utc),
        )
        lock_logs_embed.set_footer(text="PESU Bot")
        lock_logs_embed.add_field(name="Channel", value=channel.mention, inline=True)
        lock_logs_embed.add_field(
            name="Moderator", value=interaction.user.mention, inline=True
        )
        lock_logs_embed.add_field(name="Reason", value=reason, inline=False)
        mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mod_logs_id:
            return
        mod_logs_channel = self.client.get_channel(int(mod_logs_id))
        if not isinstance(mod_logs_channel, discord.TextChannel):
            return
        if mod_logs_channel:
            await mod_logs_channel.send(embed=lock_logs_embed)
        else:
            print(
                f"Mod logs channel not found: {ug.load_channel_id('MOD_LOGS', logs=True)}"
            )

    @lock_channel.error
    async def lock_channel_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This channel doesn't exist or has been deleted", ephemeral=True
                )

            elif isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to lock this channel at this time", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(
        channel="The channel to unlock (defaults to current channel)"
    )
    async def unlock_channel(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
    ):
        if not ug.has_mod_permissions(interaction.user):
            await interaction.response.send_message(
                "You think I am like dyno ah?", ephemeral=True
            )
            return

        if channel is None:
            if not isinstance(interaction.channel, discord.TextChannel):
                return await interaction.response.send_message(
                    "This command can only be used in a text channel", ephemeral=True
                )
            channel = interaction.channel

        if not interaction.guild:
            return await interaction.response.send_message(
                "This command can only be used in a server", ephemeral=True
            )
        everyone_role = interaction.guild.default_role

        overwrites = channel.overwrites_for(everyone_role)
        if overwrites.send_messages is None or overwrites.send_messages is True:
            await interaction.response.send_message(
                "This channel ain't locked bruh whatcha doin", ephemeral=True
            )
            return

        overwrites.send_messages = None
        await channel.set_permissions(everyone_role, overwrite=overwrites)
        await interaction.response.send_message(
            f"Unlocked {channel.mention}", ephemeral=False
        )

        unlock_embed = discord.Embed(
            title="Channel Unlocked :unlock:",
            color=discord.Color.green(),
            timestamp=datetime.now(dt.timezone.utc),
        )
        unlock_embed.set_footer(text="PESU Bot")
        await channel.send(embed=unlock_embed)

        unlock_logs_embed = discord.Embed(
            title="Unlock",
            color=discord.Color.green(),
            timestamp=datetime.now(dt.timezone.utc),
        )
        unlock_logs_embed.set_footer(text="PESU Bot")
        unlock_logs_embed.add_field(name="Channel", value=channel.mention, inline=True)
        unlock_logs_embed.add_field(
            name="Moderator", value=interaction.user.mention, inline=True
        )
        mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mod_logs_id:
            return
        mod_logs_channel = self.client.get_channel(int(mod_logs_id))
        if not isinstance(mod_logs_channel, discord.TextChannel):
            return
        if mod_logs_channel:
            await mod_logs_channel.send(embed=unlock_logs_embed)
        else:
            print(
                f"Mod logs channel not found: {ug.load_channel_id('MOD_LOGS', logs=True)}"
            )

    @unlock_channel.error
    async def unlock_channel_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This channel doesn't exist or has been deleted", ephemeral=True
                )

            elif isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to unlock this channel at this time", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(
        name="timeout", description="Timeout a member for a specified duration"
    )
    @app_commands.describe(
        member="The member to timeout",
        time="Duration for timeout (e.g., 1h, 30m, 2d)",
        reason="Reason for the timeout",
    )
    async def timeout_member(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        time: str,
        reason: str = "No reason provided",
    ):
        if not ug.has_mod_permissions(interaction.user):
            await interaction.response.send_message(
                "You are not authorised to do this", ephemeral=True
            )
            return

        try:
            seconds = self.parse_time(time)
        except ValueError:
            await interaction.response.send_message(
                "Mention the proper amount of time to be timed-out\nAccepted Time Format: Should end with `d/h/m/s`",
                ephemeral=True,
            )
            return

        if seconds <= 0 or seconds > 2419200:
            await interaction.response.send_message(
                "Time-out limit is 28 days only", ephemeral=True
            )
            return

        if member.is_timed_out():
            await interaction.response.send_message(
                "Brother, leave the already timed-out poor soul alone", ephemeral=True
            )
            return

        if ug.has_mod_permissions(member):
            await interaction.response.send_message(
                "Leyy, he's admin/mod. Can't time them out", ephemeral=True
            )
            return

        if member.bot:
            await interaction.response.send_message(
                "You dare time-out one of my kind nin amn", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)

        timeout_until = utcnow() + timedelta(seconds=seconds)
        await member.timeout(timeout_until, reason=reason)

        timeout_embed = discord.Embed(
            title="Time-out", color=0x8B0000, timestamp=utcnow()
        )
        timeout_embed.set_footer(text="PESU Bot")
        timeout_timestamp = int(timeout_until.timestamp())
        timeout_embed.add_field(
            name="Timed-out Member",
            value=f"{member.mention} was timed-out\nDe-time-out: <t:{timeout_timestamp}:R>\nReason: {reason}",
            inline=False,
        )

        await interaction.followup.send(embed=timeout_embed)

        mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mod_logs_id:
            return
        mod_logs = self.client.get_channel(int(mod_logs_id))
        if not isinstance(mod_logs, discord.TextChannel):
            return
        if mod_logs:
            timeout_logs_embed = discord.Embed(
                title="Time-out", color=0x8B0000, timestamp=utcnow()
            )
            timeout_logs_embed.add_field(
                name="Timed-out User",
                value=f"{member.mention}\nTime: {time}\nReason: {reason}\nModerator: {interaction.user.mention}",
                inline=False,
            )
            timeout_logs_embed.set_footer(text="PESU Bot")
            await mod_logs.send(embed=timeout_logs_embed)

    @timeout_member.error
    async def timeout_member_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This user doesn't even exist here, who are you trying to timeout?",
                    ephemeral=True,
                )

            elif isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to timeout this user at this time", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    @app_commands.command(name="detimeout", description="Remove timeout from a member")
    @app_commands.describe(member="The member to remove timeout from")
    async def detimeout_member(
        self, interaction: discord.Interaction, member: discord.Member
    ):

        if not ug.has_mod_permissions(interaction.user):
            await interaction.response.send_message(
                "You are not authorised to do this", ephemeral=True
            )
            return

        if not member.is_timed_out():
            await interaction.response.send_message(
                "This person ain't on time-out only", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)

        await member.timeout(None, reason=f"Timeout removed by {interaction.user}")

        detimeout_embed = discord.Embed(
            title="De-Time-out", color=0x00FF00, timestamp=utcnow()
        )
        detimeout_embed.set_footer(text="PESU Bot")
        detimeout_embed.add_field(
            name="De-timed-out Member",
            value=f"{member.mention}, welcome back",
            inline=False,
        )

        await interaction.followup.send(
            content=f"{member.mention}", embed=detimeout_embed
        )

        mod_logs_id = ug.load_channel_id("MOD_LOGS", logs=True)
        if not mod_logs_id:
            return
        mod_logs = self.client.get_channel(int(mod_logs_id))
        if not isinstance(mod_logs, discord.TextChannel):
            return
        if mod_logs:
            detimeout_logs_embed = discord.Embed(
                title="De-time-out", color=0x00FF00, timestamp=utcnow()
            )
            detimeout_logs_embed.set_footer(text="PESU Bot")
            detimeout_logs_embed.add_field(
                name="De-timed-out User",
                value=f"{member.mention}\nModerator: {interaction.user.mention}",
                inline=False,
            )
            await mod_logs.send(embed=detimeout_logs_embed)

    @detimeout_member.error
    @timeout_member.error
    async def detimeout_member_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.NotFound):
                await interaction.followup.send(
                    "This user doesn't even exist here, who are you trying to de-timeout?",
                    ephemeral=True,
                )

            elif isinstance(original, discord.Forbidden):
                await interaction.followup.send(
                    "I am unable to de-timeout this user at this time", ephemeral=True
                )

            else:
                await interaction.followup.send(
                    embed=ug.build_unknown_error_embed(error)
                )

        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))


async def setup(client: DiscordBot):
    await client.add_cog(
        SlashMod(client),
        guild=discord.Object(id=ug.load_config_value("GUILD", {}).get("ID")),
    )
