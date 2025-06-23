import json
import discord
from pathlib import Path

def load_config_value(key: str, default=None):
    for dir in [Path.cwd()] + list(Path.cwd().parents):
        confipath = dir / "config.json"
        if confipath.exists():
            try:
                with confipath.open("r", encoding="utf-8") as f:
                    return json.load(f).get(key, default)
            except json.JSONDecodeError:
                return default
    return default


def build_unknown_error_embed(error: Exception) -> discord.Embed:
    return discord.Embed(
        title="❗ Unexpected Error",
        description="Something went wrong while processing the command.",
        color=discord.Color.red()
    ).add_field(
        name="Error Type",
        value=type(error).__name__,
        inline=True
    ).add_field(
        name="Details",
        value=str(error)[:1000] or "No details available.",
        inline=False
    ).set_footer(
        text="Please report this to the developers if it keeps happening."
    )

def build_eval_embed(input_code: str, output: str, success: bool = True) -> discord.Embed:
    color = discord.Color.green() if success else discord.Color.red()
    title = "✅ Eval Result" if success else "❌ Eval Error"

    embed = discord.Embed(
        title=title,
        color=color
    )

    embed.add_field(name="📥 Input", value=f"```py\n{input_code}```", inline=False)
    embed.add_field(name="📤 Output", value=f"```py\n{output}```", inline=False)

    return embed