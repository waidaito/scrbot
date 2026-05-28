import discord
from discord.ext import commands
import os
from flask import Flask, request, jsonify
from threading import Thread
import asyncio

app = Flask('')

roblox_commands = {}
roblox_announcements = {}

# Lưu trữ ID kênh Discord cuối cùng mà admin dùng để nhắn tin với acc đó
chat_channels = {}
bot_instance = None

@app.route('/')
def home():
    return "Bot is alive"

@app.route('/get-command', methods=['GET'])
def get_command():
    roblox_name = request.args.get('name')
    if not roblox_name:
        return jsonify({"command": "none", "announcement": "none"})
    
    name_lower = roblox_name.lower()
    cmd = roblox_commands.get(name_lower, "none")
    if cmd != "none": roblox_commands[name_lower] = "none"
        
    announcement = roblox_announcements.get(name_lower, "none")
    if announcement != "none": roblox_announcements[name_lower] = "none"
        
    return jsonify({"command": cmd, "announcement": announcement})

# ĐƯỜNG DẪN NHẬN TIN NHẮN TỪ GAME GỬI VỀ DISCORD
@app.route('/send-chat', methods=['POST'])
def send_chat():
    data = request.json
    roblox_name = data.get('name')
    msg = data.get('message')
    
    if roblox_name and msg and bot_instance:
        name_lower = roblox_name.lower()
        channel_id = chat_channels.get(name_lower)
        if channel_id:
            channel = bot_instance.get_channel(channel_id)
            if channel:
                # Gửi tin nhắn về Discord theo dạng: name: nội dung
                asyncio.run_coroutine_threadsafe(
                    channel.send(f"💬 **{roblox_name}**: {msg}"), 
                    bot_instance.loop
                )
    return jsonify({"status": "success"})

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

# Hỗ trợ cả dấu ! và dấu . theo ý bro luôn
bot = commands.Bot(command_prefix=["!", "."], intents=intents)
bot_instance = bot

@bot.event
async def on_ready():
    print(f"Messenger Bot {bot.user} đã lên sàn!")

# 1. LỆNH KICK
@bot.command(name="kick")
async def cmd_kick(ctx, roblox_name: str, *, reason: str = "Bị admin sút!"):
    roblox_commands[roblox_name.lower()] = f"kick:{reason}"
    await ctx.send(f"🚫 Đã sút `{roblox_name}`!")

# 2. LỆNH THÔNG BÁO TO TOÀN MÀN HÌNH
@bot.command(name="thongbao")
async def cmd_thongbao(ctx, roblox_name: str, *, message: str):
    roblox_announcements[roblox_name.lower()] = f"big:{message}"
    await ctx.send(f"📢 Đã gửi thông báo lớn đến `{roblox_name}`")

# 3. LỆNH CHAT MESSENGER VỚI NGƯỜI CHƠI (!message hoặc .message)
@bot.command(name="message")
async def cmd_message(ctx, roblox_name: str, *, message: str):
    name_lower = roblox_name.lower()
    chat_channels[name_lower] = ctx.channel.id # Ghi nhớ kênh này để lát game trả lời về đây
    roblox_announcements[name_lower] = f"msg:{message}"
    await ctx.send(f"✉️ **Admin** ➔ `{roblox_name}`: {message}")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
