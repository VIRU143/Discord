import os
import discord
from discord import app_commands
from flask import Flask
from threading import Thread

# Flask app for keeping the bot alive on Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Discord Bot
class SimpleBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync commands globally
        await self.tree.sync()
        print("Slash commands synced!")

    async def on_ready(self):
        print(f'✅ Logged in as {self.user}')
        print('🚀 Bot is ready for Active Developer badge!')
        print('💡 Use /ping or /hello in your server')

bot = SimpleBot()

# Simple slash commands
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")

@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"👋 Hello {interaction.user.mention}! Keep using commands for Active Developer badge!")

@bot.tree.command(name="active", description="Info about Active Developer badge")
async def active_info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎯 Active Developer Badge",
        description="Use slash commands regularly to qualify!",
        color=0x00ff00
    )
    embed.add_field(
        name="How to get it",
        value="1. Use slash commands daily\n2. Keep bot active\n3. Wait 1-2 weeks\n4. Claim at: https://discord.com/developers/active-developer",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="user", description="Get user info")
async def user_info(interaction: discord.Interaction):
    user = interaction.user
    embed = discord.Embed(title=f"👤 {user.display_name}", color=user.accent_color or 0x7289da)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="ID", value=user.id, inline=True)
    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d"), inline=True)
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    # Start Flask server in a thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Discord bot
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables")
    else:
        bot.run(token)
