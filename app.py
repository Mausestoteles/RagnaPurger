import os
import logging

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

NEW_CHANNEL_COUNT = int(os.getenv("NEW_CHANNEL_COUNT", "50"))
NEW_CHANNEL_NAME = os.getenv("NEW_CHANNEL_NAME", "Join Rag")
NEW_CHANNEL_MESSAGE = os.getenv(
    "NEW_CHANNEL_MESSAGE",
    "@everyone Join Rag!\nhttps://discord.gg/Xj67Rt6ubW"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("purger")


class PurgerBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Commands auf Guild %s synchronisiert.", GUILD_ID)
        else:
            await self.tree.sync()
            log.info("Commands global synchronisiert.")


bot = PurgerBot()


async def _do_purge(
    interaction: discord.Interaction,
    create_fresh_channel: bool,
) -> None:
    guild = interaction.guild
    assert guild is not None

    channels = list(guild.channels)
    deleted = 0
    failed: list[str] = []

    for channel in channels:
        try:
            await channel.delete(reason=f"/Ragnapurge von {interaction.user}")
            deleted += 1
        except discord.Forbidden:
            failed.append(f"{channel.name} (keine Rechte)")
        except discord.HTTPException as exc:
            failed.append(f"{channel.name} ({exc})")

    fresh_info = ""
    if create_fresh_channel:
        created = 0
        create_errors: list[str] = []
        for _ in range(NEW_CHANNEL_COUNT):
            try:
                new_channel = await guild.create_text_channel(
                    NEW_CHANNEL_NAME,
                    reason="Purger: neuer Channel nach Purge",
                )
                if NEW_CHANNEL_MESSAGE:
                    await new_channel.send(NEW_CHANNEL_MESSAGE)
                created += 1
            except discord.HTTPException as exc:
                create_errors.append(str(exc))

        fresh_info = (
            f"\n{created} neue(r) Channel(s) mit Namen "
            f"'{NEW_CHANNEL_NAME}' erstellt."
        )
        if create_errors:
            fresh_info += "\nFehler beim Erstellen: " + ", ".join(create_errors)

    summary = f"**Fertig.** {deleted} Channel(s) geloescht.{fresh_info}"
    if failed:
        summary += "\nNicht geloescht: " + ", ".join(failed)

    try:
        await interaction.followup.send(summary, ephemeral=True)
    except discord.HTTPException:
        log.info(summary)


@bot.tree.command(
    name="Ragnapurge",
    description="Beginnt Ragnarök.",
)
@app_commands.describe(
    neuer_channel="Beginnt Ragnarök."
)
@app_commands.default_permissions(administrator=True)
@app_commands.guild_only()
async def purge(interaction: discord.Interaction, neuer_channel: bool = True) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "Dieser Command funktioniert nur auf einem Server.", ephemeral=True
        )
        return

    if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Du brauchst Administrator-Rechte fuer diesen Command.", ephemeral=True
        )
        return

    if not guild.me.guild_permissions.manage_channels:
        await interaction.response.send_message(
            "Mir fehlt die Berechtigung **Channels verwalten**. "
            "Bitte gib mir diese Rolle und versuch es erneut.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    await _do_purge(interaction, neuer_channel)


@bot.event
async def on_ready() -> None:
    log.info("Eingeloggt als %s (ID: %s)", bot.user, bot.user.id if bot.user else "?")
    if bot.application_id is not None:
        invite_url = discord.utils.oauth_url(
            bot.application_id,
            permissions=discord.Permissions(administrator=True),
            scopes=("bot", "applications.commands"),
        )
        log.info("=" * 70)
        log.info("Einladungslink (Admin-Rechte):")
        log.info("%s", invite_url)
        log.info("=" * 70)
    else:
        log.warning("Konnte keinen Einladungslink erzeugen - application_id fehlt.")

    log.info("Purger ist bereit.")


def main() -> None:
    if not TOKEN:
        raise SystemExit(
            "DISCORD_TOKEN fehlt. Lege eine .env-Datei an (siehe .env.example)."
        )
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
