import os
import discord
from discord.ext import tasks
import ccxt

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1509736189798650079

exchange = ccxt.binance()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# =========================
# SIGNAL LOGIC
# =========================

def simple_signal():
    try:
        ticker = exchange.fetch_ticker("BTC/USDT")

        price = ticker.get("last") or 0
        change = ticker.get("percentage") or 0

        if change > 0.2:
            direction = "UP 🟢"
        elif change < -0.2:
            direction = "DOWN 🔴"
        else:
            direction = "NEUTRAL ⏳"

        confidence = min(95, max(50, abs(change) * 10 + 50))

        return {
            "price": price,
            "direction": direction,
            "confidence": int(confidence),
            "change": change
        }

    except Exception as e:
        print("Signal error:", e)
        return None


# =========================
# STARTUP
# =========================

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        channel = await client.fetch_channel(CHANNEL_ID)
        await channel.send("Bot is now online ✅")
    except Exception as e:
        print("Startup channel error:", e)

    btc_loop.start()


# =========================
# LOOP
# =========================

@tasks.loop(minutes=30)
async def btc_loop():

    try:
        channel = await client.fetch_channel(CHANNEL_ID)

        data = simple_signal()

        if not data:
            print("No data returned")
            return

        embed = discord.Embed(
            title="₿ BTC SIGNAL",
            color=0x00ff00 if "UP" in data["direction"] else 0xff0000
        )

        embed.add_field(
            name="Direction",
            value=data["direction"],
            inline=False
        )

        embed.add_field(
            name="Confidence",
            value=f"{data['confidence']}%",
            inline=True
        )

        embed.add_field(
            name="Price",
            value=f"${data['price']:.2f}",
            inline=True
        )

        embed.add_field(
            name="Change",
            value=f"{data['change']}%",
            inline=False
        )

        await channel.send(embed=embed)

        print("Signal sent")

    except Exception as e:
        print("Loop error:", e)


# =========================
# RUN BOT
# =========================

client.run(TOKEN)
