import json
import discord
from datetime import datetime


def load_config_value(key: str, default=None):
    with open("config.json", "r") as f:
        config = json.load(f)
    return config.get(key, default)


def load_role_id(role_name: str) -> int | None:
    config = load_config_value("GUILD")
    if config and "ROLES" in config:
        return config["ROLES"].get(role_name, None)
    return None


def load_channel_id(channel_name: str, logs: bool = False) -> int | None:
    config = load_config_value("GUILD")
    if config and "CHANNELS" in config:
        if logs:
            return config["CHANNELS"]["LOGS"].get(channel_name, None)
        return config["CHANNELS"].get(channel_name, {}).get("ID", None)
    return None

def load_branch_id(branch_name: str) -> int | None:
    config = load_config_value("GUILD")
    if config and "ROLES" in config and "BRANCH" in config["ROLES"]:
        return config["ROLES"]["BRANCH"].get(branch_name, None)
    
def load_year_id(year: str) -> int | None:
    config = load_config_value("GUILD")
    if config and "ROLES" in config and "YEAR" in config["ROLES"]:
        return config["ROLES"]["YEAR"].get(year, None)
    


def load_campus_id(campus_name: str) -> int | None:
    config = load_config_value("GUILD")
    if config and "ROLES" in config and "CAMPUS" in config["ROLES"]:
        return config["ROLES"]["CAMPUS"].get(campus_name, None)

def build_unknown_error_embed(error: Exception) -> discord.Embed:
    return (
        discord.Embed(
            title="❗ Unexpected Error",
            description="Something went wrong while processing the command.",
            color=discord.Color.red(),
            timestamp=datetime.now(),
        )
        .add_field(name="Error Type", value=type(error).__name__, inline=True)
        .add_field(
            name="Details",
            value=str(error)[:1000] or "No details available.",
            inline=False,
        )
        .add_field(
            name="Support",
            value="Please report this to the developers if it keeps happening.",
            inline=False,
        )
        .set_footer(
            text="PESU Bot",
        )
    )


def has_mod_permissions(member):
    admin_role = discord.utils.get(member.guild.roles, id=load_role_id("ADMIN"))
    mod_role = discord.utils.get(member.guild.roles, id=load_role_id("MOD"))
    return admin_role in member.roles or mod_role in member.roles


def has_bot_dev_permissions(member):
    bot_dev_role = discord.utils.get(member.guild.roles, id=load_role_id("BOT_DEV"))
    return bot_dev_role in member.roles if bot_dev_role else False
