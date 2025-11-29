import os
import json
import asyncio
from datetime import datetime, timedelta
import logging
import discord
from discord.ext import commands
from discord import app_commands
# Removed: import concurrent.futures (since we removed file I/O)

# ---------- REQUIRED FOR RENDER ----------
from fastapi import FastAPI
import uvicorn
import threading

# ---------- ENV VARS ----------
TOKEN = os.getenv("TOKEN")
TEST_GUILD_ID = os.getenv("TEST_GUILD_ID")
# Removed: WARNINGS_FILE = os.getenv("WARNINGS_FILE", "warnings.json")

if not TOKEN:
    logging.error("TOKEN is missing! Add it in Render → Environment Variables")
    raise SystemExit("TOKEN is missing! Add it in Render → Environment Variables")

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

# ---------- BOT ----------
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
# Removed: file_lock = asyncio.Lock()
# Removed: executor = concurrent.futures.ThreadPoolExecutor(max_workers=5) 

# In-memory dictionary to store warnings (resets on restart)
# If persistent storage is needed later, this can be easily reintroduced with file I/O or a database.
in_memory_warnings = {} 


# ---------- BAD WORDS ----------
BAD_WORDS = {"badword1", "badword2", "swear1", "curse1"}

# Removed: LOAD WARNINGS (Synchronous, called once at startup)
# Removed: save_warnings (Asynchronous, non-blocking)


# ---------- UTIL ----------
def find_badwords(text):
    return [w for w in BAD_WORDS if w in text.lower()]

# ---------- ON READY ----------
@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        if TEST_GUILD_ID:
            guild = discord.Object(id=int(TEST_GUILD_ID))
            await bot.tree.sync(guild=guild)
            log.info("Synced slash commands instantly (guild)")
        else:
            await bot.tree.sync()
            log.info("Synced global slash commands")
    except Exception as e:
        log.error(f"Error syncing slash commands: {e}")

    log.info(f"{bot.user} is online!")

# ---------- SLASH COMMANDS ----------
@bot.tree.command(name="hello", description="Ping test slash command")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello! Slash command working ✔️")

@bot.tree.command(name="warnings", description="View the current warning count for a member or the full in-memory data.")
@app_commands.describe(member="The member whose warnings you want to check.", full_data="Set to True to view all in-memory warnings data for this guild (JSON).")
@app_commands.guild_only() 
async def warnings_command(interaction: discord.Interaction, member: discord.Member, full_data: bool = False):
    # Simple check: Ensure the user has permission to kick members (common moderator permission)
    if not interaction.user.guild_permissions.kick_members:
        return await interaction.response.send_message(
            "You need 'Kick Members' permission to use this command.", ephemeral=True
        )

    gid = str(interaction.guild.id)
    uid = str(member.id)

    if full_data:
        # Display full guild data in JSON format
        guild_data = in_memory_warnings.get(gid, {})
        if not guild_data:
            response = f"No warnings recorded for this guild yet in this session."
        else:
            response = f"## ⚠️ In-Memory Warnings for {interaction.guild.name}\n"
            response += "```json\n"
            response += json.dumps(guild_data, indent=2)
            response += "\n```"
        
        await interaction.response.send_message(response, ephemeral=True)
        return

    # Check warnings for a specific member
    user_warnings = in_memory_warnings.get(gid, {}).get(uid, {"warnings": 0})["warnings"]
    
    if user_warnings == 0:
        await interaction.response.send_message(
            f"✅ {member.display_name} has no warnings recorded in this session.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"⚠️ {member.display_name} has **{user_warnings}** warnings recorded in this session.", ephemeral=False
        )

# ---------- BAD WORD HANDLER ----------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    bad = find_badwords(message.content)
    if bad:
        gid = str(message.guild.id)
        uid = str(message.author.id)

        # Update in-memory storage (this data is lost when the bot restarts)
        if gid not in in_memory_warnings:
            in_memory_warnings[gid] = {}
        if uid not in in_memory_warnings[gid]:
            in_memory_warnings[gid][uid] = {"warnings": 0}

        in_memory_warnings[gid][uid]["warnings"] += 1
        current_warnings = in_memory_warnings[gid][uid]['warnings']
        
        # Delete and warn
        try:
            await message.delete()
            await message.channel.send(
                f"⚠️ {message.author.mention}, bad words detected: **{', '.join(bad)}**. You have **{current_warnings}** warnings (in this session).",
                delete_after=10
            )
        except discord.Forbidden:
            log.warning(f"Could not delete message or send warning in {message.guild.name}. Check bot permissions.")


    await bot.process_commands(message)

# ---------- FASTAPI KEEP-ALIVE (REQUIRED FOR RENDER) ----------
app = FastAPI()

@app.get("/")
def home():
    """Simple endpoint to satisfy Render's health check."""
    return {"status": "running", "bot_user": bot.user.name if bot.user else "Starting..."}

def run_fastapi():
    """Runs the Uvicorn/FastAPI server in a separate thread."""
    log.info("Starting FastAPI Uvicorn server on port 10000...")
    uvicorn.run(app, host="0.0.0.0", port=10000, log_level="warning")

# Start the web server thread
threading.Thread(target=run_fastapi, daemon=True).start()

# ---------- RUN ----------
# This command runs the main event loop for the Discord bot
bot.run(TOKEN)
