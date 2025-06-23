import io
import os
import discord
import textwrap
import contextlib
import utils.general as ug
from discord import app_commands
from discord.ext import commands



class EvalModal(discord.ui.Modal, title="Eval Command"):
    evalInput = discord.ui.TextInput(
        label="Code to evaluate",
        style=discord.TextStyle.paragraph,
        placeholder="Enter the code you want to evaluate here",
        required=True,
        max_length=2000
    )
    
    def __init__(self, client: commands.Bot, interaction: discord.Interaction):
        super().__init__()
        self.client = client
        self.main_interaction = interaction
    
    async def on_submit(self, modal_interaction: discord.Interaction):
        await modal_interaction.response.defer()
        local_variables = {
            "discord": discord,
            "commands": commands,
            "client": self.client,
            "interaction": self.main_interaction,
            "channel": self.main_interaction.channel,
            "author": self.main_interaction.user,
            "guild": self.main_interaction.guild,
        }
        
        stdout = io.StringIO()
        code = self.evalInput.value.strip()
        if not code:
            await modal_interaction.followup.send("No code provided to evaluate.", ephemeral=True)
            return
        
        try:
            with contextlib.redirect_stdout(stdout):
                exec(
                    f"async def func():\n{textwrap.indent(code, '    ')}", local_variables,
                )

                obj = await local_variables["func"]()
                result = f"{stdout.getvalue()}\n-- {repr(obj)}\n"
                evalEmbed = ug.build_eval_embed(
                    input_code=code,
                    output=result,
                    success=True
                )
        except Exception as e:
            result = f"Error: {e}\n{stdout.getvalue()}"
            evalEmbed = ug.build_eval_embed(
                input_code=code,
                output=result,
                success=False
            )
        
        delete_b = discord.ui.Button(emoji="🗑️", style=discord.ButtonStyle.red)
        
        async def delete_b_callback(button_interaction: discord.Interaction):
            if button_interaction.user.id == self.main_interaction.user.id:
                await button_interaction.message.delete()
            else:
                await button_interaction.response.send_message(
                    "You cannot delete this message.", ephemeral=True
                )

        view = discord.ui.View(timeout=60)
        delete_b.callback = delete_b_callback
        view.add_item(delete_b)
        await modal_interaction.followup.send(embed=evalEmbed, view=view, ephemeral=False)



class SlashDev(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client


    #group = app_commands.Group(name="dev", description="Commands for developers")
    
    @staticmethod
    def is_botdev():
        def predicate(interaction: discord.Interaction) -> bool:
            return any(role.id == ug.load_config_value("botDev") for role in interaction.user.roles)
        return app_commands.check(predicate)
    
    
    @app_commands.command(name="echo", description="Echoes a message to the target channel")
    @app_commands.describe(channel="The channel to send the message to", message="The message to send")
    @is_botdev()
    async def echo(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        await interaction.response.defer()
        await channel.send(message)
        await interaction.followup.send(f"Message sent to {channel.mention}")

    @echo.error
    async def echo_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.followup.send(
                "Not to you lol", ephemeral=True
            )
        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
    
    @app_commands.command(name="gitpull", description="Pulls the latest changes from the git repository")
    @is_botdev()
    async def gitpull(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # can only be run by Han or Stark
        if interaction.user.id in [723377619420184668, 718845827413442692]:
            import subprocess
            try:
                result = subprocess.run(
                    ["git", "pull"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                await interaction.followup.send(f"Git pull successful:\n{result.stdout}")
            except subprocess.CalledProcessError as e:
                await interaction.followup.send(f"Git pull failed:\n{e.stderr}")
        else:
            await interaction.followup.send(
                "You are not authorised to run this command", ephemeral=True
            )

    @gitpull.error
    async def gitpull_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        await interaction.followup.send(embed=ug.build_unknown_error_embed(error))

    
    @app_commands.command(name="eval", description="Evaluate Python code")
    @is_botdev()
    async def eval_command(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EvalModal(client=self.client, interaction=interaction))
    
    @eval_command.error
    async def eval_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.followup.send(
                "You are not authorised to run this command", ephemeral=True
            )
        else:
            await interaction.followup.send(embed=ug.build_unknown_error_embed(error))
        


async def setup(client: commands.Bot):
    await client.add_cog(
        SlashDev(client), guild=discord.Object(id=os.getenv("GUILD_ID"))
    )
