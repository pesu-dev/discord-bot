import os
import discord
import utils.general as ug
from discord.ext import commands
from discord import app_commands

class HelpEmbeds:
    def __init__(self):
        self.general = [
            discord.Embed(title="PESU Bot", description="General", color=discord.Color.dark_purple(), timestamp=discord.utils.utcnow())
            .add_field(name="Uptime", value="`/uptime`", inline=False)
            .add_field(name="Ping", value="`/ping`", inline=False)
            .add_field(name="Support", value="`/support`", inline=False),

            discord.Embed(title="PESU Bot", description="General", color=discord.Color.dark_purple(), timestamp=discord.utils.utcnow())
            .add_field(name="Poll", value="`/spotify`", inline=False)
            .add_field(name="Count", value="`/count`", inline=False)
            .add_field(name="Additional Roles", value="`/addroles`", inline=False),

            discord.Embed(title="PESU Bot", description="General", color=discord.Color.dark_purple(), timestamp=discord.utils.utcnow())
            .add_field(name="Help", value="`/help`", inline=False)
            .add_field(name="Pride", value="`/pride`", inline=False)
        ]

        self.data = [
            discord.Embed(title="PESU Bot", description="Data", color=discord.Color.dark_purple(), timestamp=discord.utils.utcnow())
            .add_field(name="Info", value="`/info`", inline=False)
            .add_field(name="Deverify", value="`/deverify`", inline=False)
            .add_field(name="File", value="`/file`", inline=False),
        ]

        self.moderation = [
            discord.Embed(title="PESU Bot", description="Moderation", color=discord.Color.dark_purple(), timestamp=discord.utils.utcnow())
            .add_field(name="Kick", value="`/kick`", inline=False)
            .add_field(name="Ban", value="`/ban`", inline=False)
            .add_field(name="Lock", value="`/lock`", inline=False),

            discord.Embed(title="PESU Bot", description="Moderation", color=discord.Color.dark_purple(), timestamp=discord.utils.utcnow())
            .add_field(name="Unlock", value="`/unlock`", inline=False)
            .add_field(name="Timeout", value="`/timeout`", inline=False)
            .add_field(name="De-Timeout", value="`/detimeout`", inline=False),

            discord.Embed(title="PESU Bot", description="Moderation", color=discord.Color.dark_purple(), timestamp=discord.utils.utcnow())
            .add_field(name="Purge", value="`/purge`", inline=False),
        ]
    def get_embeds(self, category: str):
        return getattr(self, category.lower(), self.general)
class HelpView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, category: str = "general", page: int = 0):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.category = category.lower()
        self.page = page
        self.message = None
        self.embeds = HelpEmbeds().get_embeds(self.category)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(HelpSelect(self.category))
        self.add_item(PrevButton(self))
        self.add_item(NextButton(self))

    def get_embed(self):
        embed = self.embeds[self.page]
        total_pages = len(self.embeds)
        embed.set_footer(text=f"PESU Bot | Page {self.page + 1}/{total_pages}")
        return embed
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True 

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass


class HelpSelect(discord.ui.Select):
    def __init__(self, current_category: str):
        options = [
            discord.SelectOption(label="General", value="general", emoji="🖖"),
            discord.SelectOption(label="Data", value="data", emoji="📃"),
            discord.SelectOption(label="Moderation", value="moderation", emoji="👮"),
            discord.SelectOption(label="Dev", value="dev", emoji="💻"),
        ]
        super().__init__(placeholder="Select category", options=options)
        self.current_category = current_category

    async def callback(self, interaction: discord.Interaction):
        self.view.category = self.values[0]
        self.view.page = 0
        self.view.embeds = HelpEmbeds().get_embeds(self.view.category)
        self.view.update_buttons()
        await interaction.response.edit_message(embed=self.view.get_embed(), view=self.view)


class PrevButton(discord.ui.Button):
    def __init__(self, view: HelpView):
        super().__init__(emoji="⬅️", style=discord.ButtonStyle.primary)
        self.view_ref = view
        self.disabled = view.page == 0

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.page > 0:
            self.view_ref.page -= 1
            self.view_ref.update_buttons()
            await interaction.response.edit_message(embed=self.view_ref.get_embed(), view=self.view_ref)


class NextButton(discord.ui.Button):
    def __init__(self, view: HelpView):
        super().__init__(emoji="➡️", style=discord.ButtonStyle.primary)
        self.view_ref = view
        self.disabled = view.page >= len(view.embeds) - 1

    async def callback(self, interaction: discord.Interaction):
        if self.view_ref.page < len(self.view_ref.embeds) - 1:
            self.view_ref.page += 1
            self.view_ref.update_buttons()
            await interaction.response.edit_message(embed=self.view_ref.get_embed(), view=self.view_ref)

class SlashHelp(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="help", description="Show the bot's help menu")
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if any(role.id == ug.load_role_id("just_joined") for role in interaction.user.roles):
            embed = discord.Embed(title="PESU Bot", description=f"Visit <#{ug.load_channel_id('welcomeChannel')}> to get verified first!", color=discord.Color.red(), timestamp=discord.utils.utcnow())
            embed.set_footer(text="PESU Bot")
            await interaction.followup.send(embed=embed)
            return

        view = HelpView(interaction, category="general", page=0)
        message = await interaction.followup.send(embed=view.get_embed(), view=view)
        view.message = message

    @help_command.error
    async def help_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))


async def setup(client: commands.Bot):
    await client.add_cog(SlashHelp(client), guild=discord.Object(id=ug.load_config_value("GUILD", {}).get("ID")))