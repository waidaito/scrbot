import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask, request, jsonify
from threading import Thread
import asyncio
import time

app = Flask('')

ADMIN_ID = 1219951796982648913

roblox_commands = {}
global_announcement = "none"
roblox_messages = {}
chat_admins = {}
kick_all_active = False
kick_all_reason = ""
active_players = {}

bot_instance = None

def is_admin(interaction: discord.Interaction):
    return interaction.user.id == ADMIN_ID

@app.route('/')
def home():
    return "Bot is live"

@app.route('/get-command', methods=['GET'])
def get_command():
    global global_announcement, kick_all_active, kick_all_reason
    roblox_name = request.args.get('name')
    if not roblox_name:
        return jsonify({"command": "none", "announcement": "none"})
    
    name_lower = roblox_name.lower()
    active_players[name_lower] = {"name": roblox_name, "last_seen": time.time()}
    
    if kick_all_active:
        cmd = f"kick:{kick_all_reason}"
    else:
        cmd = roblox_commands.get(name_lower, "none")
        if cmd != "none": roblox_commands[name_lower] = "none"
        
    announcement = "none"
    specific_msg = roblox_messages.get(name_lower, "none")
    
    if specific_msg != "none":
        announcement = specific_msg
        roblox_messages[name_lower] = "none"
    elif global_announcement != "none":
        announcement = global_announcement
        
    return jsonify({"command": cmd, "announcement": announcement})

@app.route('/send-chat', methods=['POST'])
def send_chat():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON data received"})
        
    roblox_name = data.get('name')
    msg = data.get('message')
    
    if roblox_name and msg and bot_instance:
        async def send_dm():
            try:
                user = await bot_instance.fetch_user(ADMIN_ID)
                if user: 
                    await user.send(f"**{roblox_name.upper()}**: {msg}")
            except Exception as e:
                print(f"Error sending DM: {e}")
        bot_instance.loop.call_soon_threadsafe(asyncio.create_task, send_dm())
    return jsonify({"status": "success"})

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
bot_instance = bot

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Admin Bot ready. Restricted to ID: {ADMIN_ID}")

@bot.tree.command(name="kick", description="Kick a player")
async def cmd_kick(interaction: discord.Interaction, roblox_name: str, reason: str = "Kicked by admin"):
    if not is_admin(interaction):
        return await interaction.response.send_message("Access denied!")
    
    roblox_commands[roblox_name.lower()] = f"kick:{reason}"
    await interaction.response.send_message(f"Kicked {roblox_name}. Reason: {reason}")

@bot.tree.command(name="kickall", description="Kick all players from the game")
async def cmd_kick_all(interaction: discord.Interaction, reason: str = "Kicked everyone by admin"):
    global kick_all_active, kick_all_reason
    if not is_admin(interaction):
        return await interaction.response.send_message("Access denied!")
    
    kick_all_active = True
    kick_all_reason = reason
    await interaction.response.send_message(f"Kicked all server players. Reason: {reason}")
    
    await asyncio.sleep(10)
    kick_all_active = False

@bot.tree.command(name="announcement", description="Global announcement")
async def cmd_announcement(interaction: discord.Interaction, message: str):
    global global_announcement
    if not is_admin(interaction):
        return await interaction.response.send_message("Access denied!")
    
    global_announcement = f"big:{message}"
    await interaction.response.send_message(f"Announcement sent: {message}")
    await asyncio.sleep(10)
    if global_announcement == f"big:{message}": global_announcement = "none"

@bot.tree.command(name="message", description="Private message to player")
async def cmd_message(interaction: discord.Interaction, roblox_name: str, message: str):
    if not is_admin(interaction):
        return await interaction.response.send_message("Access denied!")
    
    name_lower = roblox_name.lower()
    chat_admins[name_lower] = interaction.user.id
    roblox_messages[name_lower] = f"msg:{message}"
    await interaction.response.send_message(f"Message sent to {roblox_name}: {message}")

@bot.tree.command(name="listplayer", description="List all online players running the script")
async def cmd_list_player(interaction: discord.Interaction):
    if not is_admin(interaction):
        return await interaction.response.send_message("Access denied!")
    
    current_time = time.time()
    online_players = []
    
    for name_lower, info in list(active_players.items()):
        if current_time - info["last_seen"] < 10:
            online_players.append(info["name"])
        else:
            active_players.pop(name_lower, None)
            
    if not online_players:
        return await interaction.response.send_message("No players online.")
        
    player_list_str = "\n".join(f"- {player}" for player in online_players)
    await interaction.response.send_message(f"Online players list:\n{player_list_str}")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
