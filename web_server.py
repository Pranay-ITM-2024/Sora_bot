from flask import Flask, jsonify
import threading
import time
import os
from datetime import datetime
import asyncio

app = Flask(__name__)

# Bot status tracking
bot_status = {
    "status": "starting",
    "start_time": datetime.now().isoformat(),
    "last_ping": None,
    "uptime": 0,
    "total_pings": 0
}

@app.route('/')
def home():
    """Main endpoint for uptime monitoring"""
    global bot_status
    bot_status["last_ping"] = datetime.now().isoformat()
    bot_status["total_pings"] += 1
    bot_status["uptime"] = int((datetime.now() - datetime.fromisoformat(bot_status["start_time"])).total_seconds())
    
    return jsonify({
        "message": "🤖 SORABOT is alive and running!",
        "status": bot_status["status"],
        "uptime_seconds": bot_status["uptime"],
        "uptime_formatted": format_uptime(bot_status["uptime"]),
        "last_ping": bot_status["last_ping"],
        "total_pings": bot_status["total_pings"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "bot_status": bot_status["status"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/stats')
def stats():
    """Detailed stats endpoint"""
    return jsonify({
        "bot_info": {
            "name": "SORABOT",
            "version": "2.0",
            "features": [
                "Economy System",
                "Casino Games", 
                "Guild Management",
                "Stock Market",
                "Shop & Inventory",
                "Leaderboards",
                "Data Protection"
            ]
        },
        "runtime_stats": bot_status,
        "database_protected": True,
        "backup_layers": 5
    })

def format_uptime(seconds):
    """Format uptime in human readable format"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    
    if days > 0:
        return f"{days}d {hours}h {mins}m {secs}s"
    elif hours > 0:
        return f"{hours}h {mins}m {secs}s"
    elif mins > 0:
        return f"{mins}m {secs}s"
    else:
        return f"{secs}s"

def update_bot_status(status):
    """Update bot status from main bot"""
    global bot_status
    bot_status["status"] = status

def run_flask_app():
    """Run Flask app in a separate thread"""
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def start_web_server():
    """Start the web server in a background thread"""
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    print(f"🌐 Web server started on port {os.environ.get('PORT', 5000)}")
    return flask_thread