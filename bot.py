import discord
from discord import app_commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from a .env file (for local testing)
# Render will handle these via its environment settings.
load_dotenv()

# --- Configuration ---
# Get the bot token from environment variables
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    logging.error("FATAL: BOT_TOKEN environment variable is not set. Exiting.")
    exit()

# --- Discord Bot Setup ---
class MinimalBot(discord.Client):
    """
    A minimal Discord client that includes a command tree for slash commands.
    """
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # Tree is the command processor for application commands
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logging.info(f'Successfully logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="for /ping commands"
        ))
        
        # After logging in, synchronize the commands with Discord
        await self.tree.sync()
        logging.info('Slash commands synchronized successfully.')
        
    @app_commands.command(name="ping", description="Replies with Pong! This counts as an active interaction.")
    async def ping_command(self, interaction: discord.Interaction):
        """The command logic for /ping."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Respond ephemerally (only the user can see it)
        await interaction.response.send_message(
            f"Pong! Interaction successful at `{timestamp}`. \n\n"
            "**Note:** This command execution has been registered by Discord and counts towards the **Active Developer Badge** requirement!",
            ephemeral=True
        )
        logging.info(f'[Interaction] /ping command executed by {interaction.user} in {interaction.guild.name}.')


# Create bot instance with required intents (Guilds is needed for slash commands)
intents = discord.Intents.default()
intents.guilds = True
client = MinimalBot(intents=intents)


# --- Flask Web Server Setup (For Render Hosting) ---
# Render Web Services require an open port to stay alive.
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 8080)) # Use environment PORT provided by Render

@app.route('/')
def home():
    """Simple health check endpoint."""
    bot_status = f"{client.user.name} is online." if client.is_ready() else "Bot is connecting..."
    return f"<h1>Discord Bot Health Check</h1><p>Status: {bot_status}</p><p>Web server is running on port {PORT}.</p>"

def run_flask_server():
    """Runs the Flask server."""
    logging.info(f"Starting Flask web server on port {PORT}")
    # Run the Flask app on 0.0.0.0 to bind correctly in the container environment
    app.run(host='0.0.0.0', port=PORT)

# --- Main Execution ---
if __name__ == '__main__':
    # Run the Flask server in a separate thread to prevent it from blocking the bot's loop
    web_server_thread = Thread(target=run_flask_server)
    web_server_thread.start()
    
    # Run the Discord bot client (blocking call, runs indefinitely)
    try:
        client.run(TOKEN)
    except discord.errors.LoginFailure as e:
        logging.critical(f"Failed to log in: {e}")
        logging.critical("Please check your BOT_TOKEN.")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
