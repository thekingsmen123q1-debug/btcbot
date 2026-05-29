import os
import discord
from discord.ext import tasks
import ccxt

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1509736189798650079

exchange = ccxt.coinbase()

intents = discord.Intents.default()
client = discord.Client(intents=intents)


# =========================
# PREDICTION ENGINE
# =========================

def get_prediction():

    candles = exchange.fetch_ohlcv(
        "BTC/USD",
        timeframe="5m",
        limit=5
    )

    latest = candles[-1]

    open_price = latest[1]
    high_price = latest[2]
    low_price = latest[3]
    current_price = latest[4]

    move_percent = (
        (current_price - open_price)
        / open_price
    ) * 100

    candle_range = high_price - low_price

    # =========================
    # DIRECTION LOGIC
    # =========================

    direction = "NEUTRAL ⏳"
    confidence = 50

    # bullish candle
    if current_price > open_price:

        direction = "UP 🟢"

        confidence += abs(move_percent) * 120

        # strong bullish push
        if current_price > (
            open_price + (candle_range * 0.6)
        ):
            confidence += 10

    # bearish candle
    elif current_price < open_price:

        direction = "DOWN 🔴"

        confidence += abs(move_percent) * 120

        # strong bearish push
        if current_price < (
            open_price - (candle_range * 0.6)
        ):
            confidence += 10

    confidence = int(min(95, confidence))

    # =========================
    # REVERSAL LOGIC
    # =========================

    reversal = "LOW"

    if abs(move_percent) < 0.08:
        reversal = "HIGH ⚠️"

    elif abs(move_percent) < 0.2:
        reversal = "MEDIUM ⏳"

    return {
        "price": current_price,
        "open": open_price,
        "move": move_percent,
        "direction": direction,
        "confidence": confidence,
        "reversal": reversal
    }


# =========================
# BOT STARTUP
# =========================

@client.event
async def on_ready():

    print(f"Logged in as {client.user}")

    channel = await client.fetch_channel(CHANNEL_ID)

    await channel.send(
        "BTC prediction bot online ✅"
    )

    btc_loop.start()


# =========================
# LOOP
# =========================

@tasks.loop(minutes=5)
async def btc_loop():

    try:

        channel = await client.fetch_channel(CHANNEL_ID)

        data = get_prediction()

        color = 0xffff00

        if "UP" in data["direction"]:
            color = 0x00ff00

        elif "DOWN" in data["direction"]:
            color = 0xff0000

        embed = discord.Embed(
            title="₿ BTC 5M PREDICTION",
            color=color
        )

        embed.add_field(
            name="Prediction",
            value=data["direction"],
            inline=False
        )

        embed.add_field(
            name="Confidence",
            value=f"{data['confidence']}%",
            inline=True
        )

        embed.add_field(
            name="Current Price",
            value=f"${data['price']:.2f}",
            inline=True
        )

        embed.add_field(
            name="5M Candle Move",
            value=f"{data['move']:.3f}%",
            inline=True
        )

        embed.add_field(
            name="Reversal Chance",
            value=data["reversal"],
            inline=False
        )

        embed.set_footer(
            text="Live candle momentum prediction"
        )

        await channel.send(embed=embed)

        print("Prediction sent")

    except Exception as e:
        print("Loop error:", e)


# =========================
# RUN
# =========================

client.run(TOKEN)
