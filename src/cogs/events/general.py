import discord
from discord.ext import commands
from datetime import datetime
from bot import DiscordBot
from utils import general as ug


class Events(commands.Cog):
    def __init__(self, client: DiscordBot):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        bot_logs_id = ug.load_channel_id("ID", logs=True)
        if not bot_logs_id:
            return
        just_join_id = ug.load_role_id("JUST_JOINED")
        bot_logs = member.guild.get_channel(bot_logs_id)
        if not bot_logs:
            print(f"Bot logs channel not found: {bot_logs_id}")
            return
        if not just_join_id:
            return
        just_joined = member.guild.get_role(just_join_id)
        if not just_joined:
            print(f"Just joined role not found: {just_join_id}")
            return
        links_col = self.client.link_collection

        if isinstance(bot_logs, discord.TextChannel):
            await bot_logs.send(f"{member.mention} Joined!!")

        link_record = await links_col.find_one({"userId": int(member.id)})

        if link_record:
            if link_record.get("linkedAt"):
                roles_to_add = []
                
                if link_record.get("year"):
                    year_id = ug.load_year_id(link_record.get("year"))
                    if not year_id:
                        await member.add_roles(just_joined)
                    else:
                        year_role = member.guild.get_role(year_id)
                        if year_role:
                            roles_to_add.append(year_role)
                        
                if link_record.get("branch"):
                    branch_id = ug.load_branch_id(link_record.get("branch"))
                    if not branch_id:
                        await member.add_roles(just_joined)
                    else:
                        branch_role = member.guild.get_role(int(branch_id))
                        if branch_role:
                            roles_to_add.append(branch_role)
                        
                if link_record.get("campus"):
                    campus_id = ug.load_campus_id(link_record.get("campus"))
                    if not campus_id:
                        await member.add_roles(just_joined)
                    else:
                        campus_role = member.guild.get_role(int(campus_id))
                        if campus_role:
                            roles_to_add.append(campus_role)
                if roles_to_add:
                    await member.add_roles(*roles_to_add)
            else:
                if just_joined:
                    await member.add_roles(just_joined)
                await links_col.delete_one({"_id": link_record["_id"]})
        else:
            if just_joined:
                await member.add_roles(just_joined)


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        bot_logs_id = ug.load_channel_id("ID", logs=True)
        bot_logs = member.guild.get_channel(bot_logs_id) if bot_logs_id is not None else None
        if isinstance(bot_logs, discord.TextChannel):
            await bot_logs.send(f"{member.mention} Left!!")

        links_col = self.client.link_collection
        link_record = await links_col.find_one({"userId": str(member.id)})

        if link_record:
            if link_record["linkedAt"] is None:
                await links_col.delete_one({"_id": link_record["_id"]}) 
                if isinstance(bot_logs, discord.TextChannel):
                    await bot_logs.send(f"Linked record of {member.mention} has been deleted.!")

                
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        mentions = message.mentions
        role_mentions = message.role_mentions

        ghost_ping_embed = discord.Embed(
            title="Ghost Ping Alert",
            timestamp=datetime.now(),
            color=discord.Color.blue(),
        )

        if message.mention_everyone:
            ghost_ping_embed.add_field(
                name="@everyone/@here pings",
                value=f"{message.author.mention} ghost pinged `@everyone/@here` in <#{message.channel.id}>",
                inline=False,
            )

        if role_mentions:
            ping_list = ""
            for role in role_mentions:
                ping_list += f"<@&{role.id}> "
            ghost_ping_embed.add_field(
                name="Role pings",
                value=f"{message.author.mention} ghost pinged {ping_list}in <#{message.channel.id}>",
                inline=False,
            )

        user_mentions = [member for member in mentions if not member.bot]
        if user_mentions:
            ping_list = ""
            for member in user_mentions:
                ping_list += f"<@{member.id}> "
            ghost_ping_embed.add_field(
                name="Member pings",
                value=f"{message.author.mention} ghost pinged {ping_list}in <#{message.channel.id}>",
                inline=False,
            )

        if len(ghost_ping_embed.fields) > 0:
            mod_logs = message.guild.get_channel(
                ug.load_channel_id("MOD_LOGS", logs=True)
            )
            ghost_ping_embed.add_field(
                name="Message content",
                value=message.content if message.content else "No content",
                inline=False,
            )
            ghost_ping_embed.set_footer(text="PESU Bot")
            if mod_logs:
                await mod_logs.send(embed=ghost_ping_embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        old_mentions = before.mentions
        new_mentions = after.mentions
        old_role_mentions = before.role_mentions
        new_role_mentions = after.role_mentions

        if before.type == discord.MessageType.reply and before.reference:
            try:
                replied_user = before.reference.resolved.author
                if replied_user in old_mentions:
                    old_mentions = [m for m in old_mentions if m.id != replied_user.id]
            except:
                pass

        old_mention_ids = set(m.id for m in old_mentions)
        new_mention_ids = set(m.id for m in new_mentions)
        old_role_ids = set(r.id for r in old_role_mentions)
        new_role_ids = set(r.id for r in new_role_mentions)

        if (
            old_mention_ids != new_mention_ids
            or old_role_ids != new_role_ids
            or before.mention_everyone != after.mention_everyone
        ):

            ghost_ping_embed = discord.Embed(
                title="Ghost Ping Alert (Edited Message)",
                timestamp=datetime.now(),
                color=discord.Color.blue(),
            )
            ghost_ping_embed.set_footer(text="PESU Bot")
            if before.mention_everyone:
                ghost_ping_embed.add_field(
                    name="@everyone/@here pings",
                    value=f"<@{before.author.id}> ghost pinged `@everyone/@here` in <#{before.channel.id}>",
                    inline=False,
                )

            if old_role_mentions:
                ping_list = ""
                for role in old_role_mentions:
                    ping_list += f"<@&{role.id}> "
                ghost_ping_embed.add_field(
                    name="Role pings",
                    value=f"<@{before.author.id}> ghost pinged {ping_list}in <#{before.channel.id}>",
                    inline=False,
                )

            user_mentions = [member for member in old_mentions if not member.bot]
            if user_mentions:
                ping_list = ""
                for member in user_mentions:
                    ping_list += f"<@{member.id}> "
                ghost_ping_embed.add_field(
                    name="Member pings",
                    value=f"<@{before.author.id}> ghost pinged {ping_list}in <#{before.channel.id}>",
                    inline=False,
                )

            if len(ghost_ping_embed.fields) > 0:
                ghost_ping_embed.add_field(
                    name="Jump URL", value=before.jump_url, inline=False
                )

                mod_logs = before.guild.get_channel(
                    ug.load_channel_id("MOD_LOGS", logs=True)
                )
                if mod_logs:
                    await mod_logs.send(embed=ghost_ping_embed)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        await thread.join()


async def setup(client: DiscordBot):
    await client.add_cog(Events(client))
