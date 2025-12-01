# keep_alive.py
from flask import Flask, jsonify
from threading import Thread
import requests
import time
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Render URL from environment or use default
RENDER_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://your-bot-name.onrender.com')

class RenderKeeper:
    def __init__(self):
        self.is_running = True
        
    def ping_self(self):
        """Ping the Render service to keep it awake"""
        while self.is_running:
            try:
                response = requests.get(RENDER_URL, timeout=10)
                if response.status_code == 200:
                    logger.info("✅ Successfully pinged Render service")
                else:
                    logger.warning(f"⚠️ Ping returned status {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Failed to ping: {e}")
            
            # Ping every 8 minutes (Render sleeps after 15 minutes of inactivity)
            time.sleep(480)  # 8 minutes
    
    def start(self):
        """Start the ping service"""
        ping_thread = Thread(target=self.ping_self, daemon=True)
        ping_thread.start()
        logger.info("🚀 Started Render keep-alive service")

# Create and start keeper
keeper = RenderKeeper()

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Discord Bot",
        "host": "Render.com",
        "keep_alive": "active",
        "ping_url": RENDER_URL
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

@app.route('/ping')
def ping():
    return "pong"

@app.route('/info')
def info():
    return jsonify({
        "platform": "Render",
        "tier": "Free",
        "sleep_prevention": "Active",
        "ping_interval": "8 minutes",
        "endpoints": ["/", "/health", "/ping", "/info"]
    })

def keep_alive():
    """Start the Flask server and ping service"""
    # Start ping service
    keeper.start()
    
    # Start Flask server in a separate thread
    def run_flask():
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask server started on port 8080")
