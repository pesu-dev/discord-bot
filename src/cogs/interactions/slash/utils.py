import os
import discord
import utils.general as ug
from discord import app_commands, Interaction, SelectOption
from discord.ext import commands


class RoleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            SelectOption(label="None", value="0", description="Use this to de-select your choice in this menu"),
            SelectOption(label="Gamer", value="778825985361051660", description="Don't ever question Minecraft logic", emoji="🎮"),
            SelectOption(label="Coder", value="778875127257104424", description="sudo apt install system32", emoji="⌨️"),
            SelectOption(label="Musician", value="778875199701385216", description="From Pink Floyd to Prateek Kuhad", emoji="🎸"),
            SelectOption(label="Editor", value="782642024071168011", description="A peek behind-the-scenes", emoji="🎥"),
            SelectOption(label="Tech", value="790106229997174786", description="Pure Linus Sex Tips", emoji="💡"),
            SelectOption(label="Moto", value="836652197214421012", description="Stutututu", emoji="⚙️"),
            SelectOption(label="Investors", value="936886064361144360", description="Stocks and Crypto are your friends", emoji="💸"),
            SelectOption(label="PESU Bot Dev", value="810507351063920671", description="Contribute to developing PESU Bot", emoji="🤖"),
            SelectOption(label="NSFW", value="778820724424704011", description="Definitely not safe for anything", emoji="👀")
        ]
        super().__init__(
            placeholder="Additional Roles",
            custom_id="add_roles_select",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        member = interaction.user
        role_id = self.values[0]

        if any(role.id == ug.load_config_value("just_joined") for role in member.roles):
            await interaction.followup.send("You need to verify yourself first.")
            return

        if role_id == "0":
            await interaction.followup.send("OK")
            return

        role = interaction.guild.get_role(int(role_id))
        if not role:
            await interaction.followup.send("Role not found")
            return

        if role in member.roles:
            await member.remove_roles(role)
            await interaction.followup.send(f"Role `{role.name}` was already present. Removing now...")
        else:
            await member.add_roles(role)
            await interaction.followup.send(f"You now have the `{role.name}` role")


class RoleSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())


class SlashUtils(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.client.add_view(RoleSelectView())
    

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
                common_members = set(roleObjects[0].members) # get the members of the first role
                for role in roleObjects[1:]: # iterate thrrough the rest of the roles skipping the first one since we already have its members
                    common_members &= set(role.members) # & is an intersection operator, basically the intersection you did in math class 11 set theory
                
                # list.extend() for sets would be set.union() or set.update() but we don't need that here
                memberCounts = len(common_members)

                roleNames = [role.name for role in roleObjects]
                wrd = "have" if memberCounts > 1 or memberCounts == 0 else "has"
                pluralorsingle = "people" if memberCounts > 1 or memberCounts == 0 else "person"
                await interaction.followup.send(content=f"{memberCounts} {pluralorsingle} {wrd} [{', '.join(roleNames)}]")


        
    

    @count.error
    async def uptime_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error)) 
    
    

    @app_commands.command(name="spotify", description="Get your current Spotify details")
    @app_commands.describe(user="The user to get Spotify details for (default: you)")
    async def spotify(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()
        realuser = interaction.guild.get_member(user.id if user else interaction.user.id) # note to self, interactions dont recieve presence data, so fetch the user via bot cache; this what i understood so far

        if realuser is None:
            await interaction.followup.send(
                content="User not found in this server.", ephemeral=True
            )
            return
        
        """print(realuser, type(realuser))
        print(f"[DEBUG] user.activities = {realuser.activities}")
        for activity in user.activities:
            print(f"[DEBUG] Activity object: {activity}")
            print(f"Type: {type(activity)}")
            print(f"Attributes: {dir(activity)}")"""
        
        for activity in realuser.activities:
            if isinstance(activity, discord.Spotify):
                await interaction.followup.send(
                    content=f"Listening to `{activity.title}` by `{activity.artist}`\nSong link: {activity.track_url}",
                    ephemeral=False
                )
                return
        await interaction.followup.send(
            content="No spotify activity detected",
            ephemeral=True
        )

    @spotify.error
    async def spotify_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
    

    
    @app_commands.command(name="addroles", description="Pick up additional roles to get access to more channels")
    @app_commands.describe(channel="The channel to send the role selection in (default: current channel)")
    async def addroles_command(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await interaction.response.defer()
        if not ug.has_mod_permissions(interaction.user):
            await interaction.followup.send(
                content="Not to you lol", ephemeral=True
            )
            return
        embe = discord.Embed(
            title="Additional Roles",
        description="Pick up additional roles to get access to more channels",
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow())


        channel = interaction.channel if channel is None else channel
        view = RoleSelectView()
        await channel.send(embed=embe, view=view)
        await interaction.followup.send(
            content=f"Role selection sent in {channel.mention}",
            ephemeral=True
        )
    
    @addroles_command.error
    async def addroles_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    


async def setup(client: commands.Bot):
    await client.add_cog(
        SlashUtils(client), guild=discord.Object(id=os.getenv("GUILD_ID"))
    )
