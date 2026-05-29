import os
import discord
from discord.ext import tasks, commands
import ccxt

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1509736189798650079

exchange = ccxt.coinbase()

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

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

    # =========================
    # PRICE TARGET PREDICTION
    # =========================

    predicted_move = move_percent * 1.8

    predicted_price = current_price + (
        current_price * (predicted_move / 100)
    )

    # =========================
    # DIRECTION LOGIC
    # =========================

    direction = "NEUTRAL ⏳"
    confidence = 50

    if current_price > open_price:
        direction = "UP 🟢"
        confidence += abs(move_percent) * 120

    elif current_price < open_price:
        direction = "DOWN 🔴"
        confidence += abs(move_percent) * 120

    confidence = int(min(95, confidence))

    # =========================
    # REVERSAL LOGIC
    # =========================

    reversal = "LOW 🔵"

    if abs(move_percent) < 0.08:
        reversal = "HIGH ⚠️"

    elif abs(move_percent) < 0.2:
        reversal = "MEDIUM ⏳"

    return {
        "price": current_price,
        "predicted_price": predicted_price,
        "move": move_percent,
        "direction": direction,
        "confidence": confidence,
        "reversal": reversal
    }


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    try:
        channel = await bot.fetch_channel(CHANNEL_ID)

        await channel.send(
            "BTC prediction bot online ✅"
        )

    except Exception as e:
        print("Startup error:", e)

    btc_loop.start()


# =========================
# AUTO PREDICTION LOOP
# =========================

@tasks.loop(minutes=5)
async def btc_loop():

    try:

        channel = await bot.fetch_channel(CHANNEL_ID)

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
            name="Predicted Price",
            value=f"${data['predicted_price']:.2f}",
            inline=False
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
            text="Live BTC momentum prediction model"
        )

        await channel.send(embed=embed)

        print("Prediction sent")

    except Exception as e:
        print("Loop error:", e)


# =========================
# SLASH COMMAND
# =========================

@bot.slash_command(
    name="btc",
    description="Get instant BTC prediction"
)
async def btc(ctx):

    data = get_prediction()

    embed = discord.Embed(
        title="₿ LIVE BTC PREDICTION",
        color=0x00ff00
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
        name="Predicted Price",
        value=f"${data['predicted_price']:.2f}",
        inline=False
    )

    embed.add_field(
        name="Reversal Chance",
        value=data["reversal"],
        inline=False
    )

    await ctx.respond(embed=embed)


# =========================
# RUN BOT
# =========================

bot.run(TOKEN)
