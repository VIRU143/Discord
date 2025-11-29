import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager
import datetime
import logging

# Set up logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# --- Configuration ---
TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.environ.get('PORT', 8000)) # Use environment PORT provided by Render
HOST = os.environ.get('HOST', '0.0.0.0')

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
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logging.info(f'Successfully logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="for /ping commands"
        ))
        
        # Synchronize commands globally (only needs to be done once per change)
        await self.tree.sync()
        logging.info('Slash commands synchronized successfully.')
        
    @app_commands.command(name="ping", description="Replies with Pong! This interaction counts for the Active Developer Badge.")
    async def ping_command(self, interaction: discord.Interaction):
        """The command logic for /ping."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        await interaction.response.send_message(
            f"Pong! Interaction successful at `{timestamp}`. \n\n"
            "**Active Developer Badge Note:** This command execution has been registered with Discord!",
            ephemeral=True
        )
        logging.info(f'[Interaction] /ping command executed by {interaction.user}.')

# Create bot instance with required intents
intents = discord.Intents.default()
intents.guilds = True # Required for slash commands
client = MinimalBot(intents=intents)

# --- FastAPI Setup ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifecycle of the Discord bot client within the FastAPI event loop.
    Starts the bot client when the server starts and stops it when the server shuts down.
    """
    logging.info("FastAPI Server Startup: Starting Discord client task...")
    
    # Start the Discord client in a separate background task
    # Note: We use client.start() instead of client.run() which is blocking
    client_task = asyncio.create_task(client.start(TOKEN))
    
    yield # Server is ready to receive requests
    
    # --- Server Shutdown ---
    logging.info("FastAPI Server Shutdown: Closing Discord client...")
    if not client.is_closed():
        await client.close()
    
    # Cancel the Discord client task
    client_task.cancel()
    
    logging.info("FastAPI Server Shutdown: Cleanup complete.")


# Initialize the FastAPI application using the defined lifespan
app = FastAPI(
    title="Discord Active Developer Bot API",
    version="1.0.0",
    description="Minimal Web Service to host an asynchronous Discord Bot on Render.",
    lifespan=lifespan
)

@app.get("/")
async def health_check():
    """Endpoint for Render's health check."""
    return {
        "status": "online",
        "bot_user": str(client.user) if client.is_ready() else "Connecting...",
        "message": "The Discord bot is running and listening for interactions."
    }

# This file does not run uvicorn.run() directly. 
# The Render Start Command will execute Uvicorn via the command line.
# See README.md for the correct Start Command.
