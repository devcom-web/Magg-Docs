# take as free will.
import discord
from discord.ext import commands
from lupa import LuaRuntime
import asyncio
import time
import re
import io
import json
from multiprocessing import Process, Queue
from datetime import datetime

BOT_TOKEN = "MTQ3NDkyMTYzMzUyODY4MDQ1OA.GGi6QU.R9HmIMWlK0M6x_O8BDojjeiEm2f-f2V783KtVk"
EXECUTION_TIMEOUT = 5
MAX_FILE_SIZE = 2 * 1024 * 1024
INSTRUCTION_LIMIT = 5000000
AUTHORIZED_USER_ID = 1453785588313620603

import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def write_log_files(code, output, env_info):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    original_path = os.path.join(LOG_DIR, f"{timestamp}_original.lua")
    output_path = os.path.join(LOG_DIR, f"{timestamp}_output.txt")
    envlog_path = os.path.join(LOG_DIR, f"{timestamp}_envlog.lua")

    with open(original_path, "w", encoding="utf-8") as f:
        f.write(code)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    with open(envlog_path, "w", encoding="utf-8") as f:
        f.write(env_info)

    return original_path, output_path, envlog_path

STATUS_MESSAGES = [
    "Best Lua Execution Tool",
    "Neptune.gg",
    "Use Neptune For Free Today!",
    "Neptune Engine v1.0",
    "Fast • Secure • Powerful"
]

async def rotate_status():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for message in STATUS_MESSAGES:
            await bot.change_presence(
                status=discord.Status.idle,
                activity=discord.Game(name=message)
            )
            await asyncio.sleep(3)

import random

AI_GUESSES = [
    "Neptune Engine: This code looks aggressive.",
    "Neptune Engine: I sense a loop-heavy structure.",
    "Neptune Engine: This might produce multiple outputs.",
    "Neptune Engine: Conditional logic detected.",
    "Neptune Engine: This script feels experimental.",
    "Neptune Engine: Execution should complete successfully.",
    "Neptune Engine: Possible high instruction usage.",
    "Neptune Engine: Minimalistic but effective."
]

def generate_ai_guess(code):
    guess = random.choice(AI_GUESSES)

    if "while" in code or "for" in code:
        guess = "Neptune AI Engine: Loop detected. Monitoring instruction usage..."

    elif "if" in code:
        guess = "Neptune AI Engine: Conditional branching detected."

    elif "function" in code:
        guess = "Neptune AI Engine: Function-based architecture detected."

    return guess

USAGE_FILE = "usage.json"
MONTHLY_LIMIT = 45
UNLIMITED_USER_ID = 1453785588313620603

try:
    with open(USAGE_FILE, "r") as f:
        usage_data = json.load(f)
except:
    usage_data = {}

def save_usage():
    with open(USAGE_FILE, "w") as f:
        json.dump(usage_data, f, indent=4)

def get_month_key():
    now = datetime.utcnow()
    return f"{now.year}-{now.month}"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot_locked = True
total_executions = 0
user_last_execution = {}

@bot.check
async def global_lock_check(ctx):
    if bot_locked:
        await ctx.send("🚫 The bot is not activated yet.")
        return False
    return True

REQUIRED_GUILD_ID = 1391025922789867590
REQUIRED_ROLE_ID = 1391119532310925513

@bot.check
async def access_control_check(ctx):
    # Unlimited user bypass
    if ctx.author.id == UNLIMITED_USER_ID:
        return True

    # DM usage
    if isinstance(ctx.channel, discord.DMChannel):
        guild = bot.get_guild(REQUIRED_GUILD_ID)
        if not guild:
            await ctx.send("❌ Guild not found.")
            return False

        member = guild.get_member(ctx.author.id)
        if not member:
            await ctx.send("❌ You must be a member of the authorized server to use DMs.")
            return False

        role = guild.get_role(REQUIRED_ROLE_ID)
        if role not in member.roles:
            await ctx.send("❌ You need the required role to use the bot in DMs.")
            return False

        return True

    # Channel usage
    if ctx.guild.id != REQUIRED_GUILD_ID:
        await ctx.send("❌ You are not in the authorized server.")
        return False

    if ctx.channel.id != REQUIRED_CHANNEL_ID:
        await ctx.send("❌ You can only use this bot in the authorized channel.")
        return False

    return True

@bot.event
async def on_ready():
    global bot_locked

    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Game(name="Awaiting confirmation...")
    )

    try:
        user = await bot.fetch_user(AUTHORIZED_USER_ID)

        await user.send(
            "⚠️ The bot has started.\nReply with **yes** within 60 seconds to activate."
        )

        def check(m):
            return (
                m.author.id == AUTHORIZED_USER_ID
                and isinstance(m.channel, discord.DMChannel)
                and m.content.lower() == "yes"
            )

        await bot.wait_for("message", timeout=60.0, check=check)

        bot_locked = False
        await user.send("✅ Bot activated.")
        print("Bot unlocked.")

        bot.loop.create_task(rotate_status())

    except Exception as e:
        print("Startup confirmation failed:", e)

class LuaEnvironment:
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.output_buffer = []
        self._setup()

    def _setup(self):
        globals_table = self.lua.globals()

        def py_print(*args):
                formatted = []
                for a in args:
                    if isinstance(a, bool):
                        formatted.append("true" if a else "false")
                    else:
                        formatted.append(str(a))
                self.output_buffer.append(" ".join(formatted))

        globals_table["print"] = py_print
        globals_table["warn"] = lambda *args: py_print("[WARN]", *args)

        self.lua.execute(f"""
        _G = _G or {{}}
        _G._G = _G
        _G._ENV = _G
        shared = _G
        _ENV = _G
        loadstring = load
        typeof = typeof or type
        _VERSION = "Lua 5.4"

        -- Protect global table
        setmetatable(_G, {{
            __newindex = function(t, k, v)
                rawset(t, k, v)
            end
        }})

        -- Executor Identity System

        EXECUTOR_NAME = "Neptune Engine"
        EXECUTOR_VERSION = "1.0.0"
        EXECUTOR_IDENTITY = "Current identity is: 6"

        function identifyexecutor()
            return EXECUTOR_NAME, EXECUTOR_VERSION
        end

        function getexecutorname()
            return EXECUTOR_NAME
        end

        function getexecutorversion()
            return EXECUTOR_VERSION
        end

        function getidentity()
            return EXECUTOR_IDENTITY
        end

        function getthreadidentity()
            return EXECUTOR_IDENTITY
        end

        function setthreadidentity(id)
            -- Locked to 6 for security
            return EXECUTOR_IDENTITY
        end

        -- Clean error formatting
        local original_error = error
        function error(msg)
            original_error(tostring(msg), 0)
        end

         -- Clean error formatting

        local original_error = error

        function error(msg)
            original_error(tostring(msg), 0)
        end

        collectgarbage("setpause", 100)
        collectgarbage("setstepmul", 200)

        function getgenv() return _G end
        function getrenv() return _G end
        function getsenv(obj) return _G end
        function getfenv(arg) return _G end
        function setfenv(fn, env) return fn end

        function getrawmetatable(obj)
            return getmetatable(obj)
        end

        function setrawmetatable(obj, mt)
            return setmetatable(obj, mt)
        end

        function newproxy(mt)
            local proxy = {{}}
            if mt then
                if mt == true then
                    setmetatable(proxy, {{}})
                else
                    setmetatable(proxy, mt)
                end
            end
            return proxy
        end

        function coroutine.wrap(f)
            local co = coroutine.create(f)
            return function(...)
                local ok, result = coroutine.resume(co, ...)
                if not ok then error(result) end
                return result
            end
        end

        local instruction_count = 0
        debug.sethook(function()
            instruction_count = instruction_count + 1
            if instruction_count > {INSTRUCTION_LIMIT} then
                error("Execution stopped: too many instructions")
            end
        end, "", 1)
        """)

    def execute(self, code):
        self.output_buffer.clear()
        try:
            wrapped = f"""
            local user_env = {{}}
            setmetatable(user_env, {{ __index = _G }})

            local chunk, err = load([===[{code}]===], nil, "t", user_env)
            if not chunk then error(err) end
            return chunk()
            """
            self.lua.execute(wrapped)
        except Exception as e:
            return "\n".join(self.output_buffer) + "\n" + str(e)

        return "\n".join(self.output_buffer)

def run_lua_process(code, queue):
    try:
        env = LuaEnvironment()
        output = env.execute(code)

        env_info = (
            f"-- Executor Info --\n"
            f"Name: Neptune Engine\n"
            f"Version: 1.0.0\n"
            f"Instruction Limit: {INSTRUCTION_LIMIT}\n"
            f"Timestamp (UTC): {datetime.utcnow()}\n"
        )

        queue.put(("success", output, env_info))
    except Exception as e:
        queue.put(("error", str(e), ""))

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

@bot.command()
async def gen(ctx):
    user_id = ctx.author.id
    month_key = get_month_key()

    if user_id == UNLIMITED_USER_ID:
        await ctx.send("♾️ You have unlimited executions.")
        return

    if str(user_id) not in usage_data:
        usage_data[str(user_id)] = {}

    if month_key not in usage_data[str(user_id)]:
        usage_data[str(user_id)][month_key] = 0

    used = usage_data[str(user_id)][month_key]
    remaining = MONTHLY_LIMIT - used

    await ctx.send(f"📊 You have **{remaining}** executions left this month.")

@bot.command()
async def ex(ctx, *, code: str = None):
    global total_executions, user_last_execution

    user_id = ctx.author.id
    month_key = get_month_key()

    if user_id != UNLIMITED_USER_ID:
        if str(user_id) not in usage_data:
            usage_data[str(user_id)] = {}

        if month_key not in usage_data[str(user_id)]:
            usage_data[str(user_id)][month_key] = 0

        if usage_data[str(user_id)][month_key] >= MONTHLY_LIMIT:
            await ctx.send("❌ You have reached your 45 executions for this month.")
            return

        usage_data[str(user_id)][month_key] += 1
        save_usage()

    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.size > MAX_FILE_SIZE:
            await ctx.send("File too large.")
            return
        raw = await attachment.read()
        code = raw.decode("utf-8", errors="ignore")

    if not code:
        await ctx.send("Usage: !ex <lua code> or attach a file.")
        return

    ai_message = generate_ai_guess(code)
    await ctx.send(ai_message)

    start = time.perf_counter()

    queue = Queue()
    p = Process(target=run_lua_process, args=(code, queue))
    p.start()
    p.join(EXECUTION_TIMEOUT)

    if p.is_alive():
        p.terminate()
        p.join()
        success = False
        output = "Execution timed out."
        env_info = ""
    else:
        if not queue.empty():
            status, result, env_info = queue.get()
            success = status == "success"
            output = result
        else:
            success = False
            output = "No output returned."
            env_info = ""

    elapsed = round(time.perf_counter() - start, 3)
    total_executions += 1
    user_last_execution[ctx.author.id] = datetime.utcnow()

    lines = len(code.split("\n"))
    chars = len(code)
    loops = len(re.findall(r'\bwhile\b|\bfor\b', code))
    conditionals = len(re.findall(r'\bif\b', code))

    status_icon = "✅" if success else "❌"
    preview = output[:1800] if output else "(no output)"

    message_text = (
        f"{status_icon} Execution {'succeeded' if success else 'failed'} ({elapsed}s)\n\n"
        f"```{preview}```\n\n"
        f"Code Statistics:\n"
        f"• Lines: {lines}\n"
        f"• Characters: {chars}\n"
        f"• Loops: {loops}\n"
        f"• Conditionals: {conditionals}"
    )

    await ctx.send(message_text)

    original_path, output_path, envlog_path = write_log_files(code, output, env_info)

    await ctx.send(
        files=[
            discord.File(original_path, filename="original.lua"),
            discord.File(output_path, filename="output.txt"),
            discord.File(envlog_path, filename="envlog.lua"),
        ]
    )

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
