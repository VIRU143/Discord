# main.py - Render.com version
import discord
from discord.ext import commands, tasks
import os
import sys
import asyncio
from keep_alive import keep_alive
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keep Render alive
keep_alive()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Activity rotation for visibility
activities = [
    discord.Game(name="with slash commands"),
    discord.Activity(type=discord.ActivityType.watching, name="for !help"),
    discord.Activity(type=discord.ActivityType.listening, name="/ping")
]

@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} is online!')
    logger.info(f'🤖 Bot ID: {bot.user.id}')
    
    # Start activity rotation
    change_status.start()
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        logger.error(f'❌ Failed to sync commands: {e}')

# Rotate status every 30 minutes
@tasks.loop(minutes=30)
async def change_status():
    current = getattr(change_status, "current", 0)
    await bot.change_presence(activity=activities[current])
    change_status.current = (current + 1) % len(activities)

# Ping command
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🏓 **Pong!**\n"
        f"• **Latency:** {latency}ms\n"
        f"• **Uptime:** <t:{int(bot.start_time.timestamp())}:R>"
    )

# Badge info command
@bot.tree.command(name="badge", description="Get Active Developer Badge info")
async def badge(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎖️ Active Developer Badge",
        description=(
            "**How to get the badge:**\n"
            "1. Create and use a slash command (like this one!)\n"
            "2. Wait 24 hours\n"
            "3. Claim at: https://discord.com/developers/active-developer\n"
            "4. Badge will appear in your profile within 24h"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="This bot is hosted 24/7 on Render.com")
    await interaction.response.send_message(embed=embed)

# Manual sync command
@bot.command()
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Slash commands synced!")

# Health check command
@bot.tree.command(name="health", description="Check bot health")
async def health(interaction: discord.Interaction):
    import psutil
    import datetime
    
    ram = psutil.virtual_memory()
    uptime = datetime.datetime.now() - bot.start_time
    
    embed = discord.Embed(
        title="🤖 Bot Health Status",
        color=discord.Color.blue()
    )
    embed.add_field(name="📶 Ping", value=f"{round(bot.latency * 1000)}ms")
    embed.add_field(name="⏱️ Uptime", value=str(uptime).split('.')[0])
    embed.add_field(name="💾 RAM", value=f"{ram.percent}% used")
    embed.add_field(name="🖥️ Host", value="Render.com (Free Tier)")
    embed.add_field(name="🔧 Status", value="✅ Operational")
    
    await interaction.response.send_message(embed=embed)

# Start bot
if __name__ == "__main__":
    bot.start_time = discord.utils.utcnow()
    
    # Get token from environment
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in environment variables!")
        sys.exit(1)
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
