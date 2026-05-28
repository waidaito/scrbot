import discord
from discord.ext import commands
import os
from flask import Flask, request, jsonify
from threading import Thread

app = Flask('')

roblox_commands = {}
roblox_announcements = {}

@app.route('/')
def home():
    return "Bot is alive"

@app.route('/get-command', methods=['GET'])
def get_command():
    # Nhận diện bằng tham số name thay vì user_id
    roblox_name = request.args.get('name')
    if not roblox_name:
        return jsonify({"command": "none", "announcement": "none"})
    
    # Chuyển tên về chữ thường để tránh lỗi viết hoa/thường
    name_lower = roblox_name.lower()
    
    cmd = roblox_commands.get(name_lower, "none")
    if cmd != "none":
        roblox_commands[name_lower] = "none"
        
    announcement = roblox_announcements.get(name_lower, "none")
    if announcement != "none":
        roblox_announcements[name_lower] = "none"
        
    return jsonify({
        "command": cmd,
        "announcement": announcement
    })

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Test Bot {bot.user} is ready!")

# LỆNH: !jump [Tên_Roblox] (Ví dụ: !jump admin123)
@bot.command(name="jump")
async def cmd_jump(ctx, roblox_name: str):
    roblox_commands[roblox_name.lower()] = "jump"
    await ctx.send(f"🔹 Đã gửi lệnh nhảy (!jump) cho Roblox Name: `{roblox_name}`")

# LỆNH: !thongbao [Tên_Roblox] [Nội dung]
@bot.command(name="thongbao")
async def cmd_thongbao(ctx, roblox_name: str, *, message: str):
    roblox_announcements[roblox_name.lower()] = message
    await ctx.send(f"📢 Đã gửi thông báo đến Roblox Name `{roblox_name}`")

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))

