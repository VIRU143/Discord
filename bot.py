import os
import json
import asyncio
from datetime import datetime, timedelta
import logging
import discord
from discord.ext import commands
from discord import app_commands

# ---------- REQUIRED FOR RENDER ----------
from fastapi import FastAPI
import uvicorn
import threading

# ---------- ENV VARS ----------
TOKEN = os.getenv("TOKEN")
TEST_GUILD_ID = os.getenv("TEST_GUILD_ID")
WARNINGS_FILE = os.getenv("WARNINGS_FILE", "warnings.json")

if not TOKEN:
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
file_lock = asyncio.Lock()

# ---------- BAD WORDS ----------
BAD_WORDS = {"badword1", "badword2", "swear1", "curse1"}

# ---------- LOAD WARNINGS ----------
def load_json(path):
    try:
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)
    except:
        return {}

warnings_data = load_json(WARNINGS_FILE)

async def save_warnings(data):
    async with file_lock:
        with open(WARNINGS_FILE, "w", encoding="utf8") as f:
            json.dump(data, f, indent=4)

# ---------- UTIL ----------
def find_badwords(text):
    return [w for w in BAD_WORDS if w in text.lower()]

# ---------- ON READY ----------
@bot.event
async def on_ready():
    try:
        if TEST_GUILD_ID:
            guild = discord.Object(id=int(TEST_GUILD_ID))
            await bot.tree.sync(guild=guild)
            log.info("Synced slash commands instantly (guild)")
        else:
            await bot.tree.sync()
            log.info("Synced global slash commands")
    except Exception as e:
        log.error(e)

    log.info(f"{bot.user} is online!")

# ---------- SLASH COMMAND ----------
@bot.tree.command(name="hello", description="Ping test slash command")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello! Slash command working ✔️")

# ---------- BAD WORD HANDLER ----------
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    bad = find_badwords(message.content)
    if bad:
        gid = str(message.guild.id)
        uid = str(message.author.id)

        if gid not in warnings_data:
            warnings_data[gid] = {}
        if uid not in warnings_data[gid]:
            warnings_data[gid][uid] = {"warnings": 0}

        warnings_data[gid][uid]["warnings"] += 1
        await save_warnings(warnings_data)

        await message.delete()
        await message.channel.send(
            f"⚠️ {message.author.mention}, bad words detected: {', '.join(bad)}"
        )

    await bot.process_commands(message)

# ---------- FASTAPI KEEP-ALIVE (REQUIRED FOR RENDER) ----------
app = FastAPI()

@app.get("/")
def home():
    return {"status": "running"}

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=10000)

threading.Thread(target=run_fastapi).start()

# ---------- RUN ----------
bot.run(TOKEN)
