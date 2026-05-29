import discord
from discord.ext import tasks
from discord.commands import Option
import ccxt
import pandas as pd
from ta.momentum import RSIIndicator

# =========================
# CONFIG
# =========================

TOKEN = "MTUwOTczODE0NTY1NzM4OTI1OA.GjwoVg.UioTdMG4K4YzEZb6-_HEwO0L4vdgw6urGuZIcs"
CHANNEL_ID = 1509736189798650079

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

# =========================
# EXCHANGE
# =========================

exchange = ccxt.coinbase()

# =========================
# SETTINGS
# =========================

update_minutes = 30

# =========================
# MARKET DATA
# =========================

def get_market_data():

    candles = exchange.fetch_ohlcv(
        'BTC/USD',
        timeframe='1m',
        limit=100
    )

    df = pd.DataFrame(candles, columns=[
        'timestamp',
        'open',
        'high',
        'low',
        'close',
        'volume'
    ])

    df['close'] = df['close'].astype(float)

    # RSI
    rsi = RSIIndicator(df['close'], window=14)
    df['rsi'] = rsi.rsi()

    # EMA
    df['ema_fast'] = df['close'].ewm(span=9).mean()
    df['ema_slow'] = df['close'].ewm(span=21).mean()

    return df

# =========================
# PREDICTION ENGINE
# =========================

def get_prediction():

    df = get_market_data()
    latest = df.iloc[-1]

    price = float(latest['close'])
    rsi = float(latest['rsi'])

    bullish = latest['ema_fast'] > latest['ema_slow']
    bearish = latest['ema_fast'] < latest['ema_slow']

    trend = "NEUTRAL ➖"
    prediction = "UP 🟢"
    confidence = 50

    # =========================
    # ALWAYS-PREDICT ENGINE
    # =========================

    if bullish:

        trend = "BULLISH 📈"

        if rsi < 40:
            prediction = "STRONG UP 🚀"
            confidence = 85

        elif rsi < 55:
            prediction = "UP 🟢"
            confidence = 72

        else:
            prediction = "WEAK UP 🟢"
            confidence = 60

    elif bearish:

        trend = "BEARISH 📉"

        if rsi > 60:
            prediction = "STRONG DOWN 🔥"
            confidence = 85

        elif rsi > 45:
            prediction = "DOWN 🔴"
            confidence = 72

        else:
            prediction = "WEAK DOWN 🔴"
            confidence = 60

    return {
        "price": price,
        "rsi": rsi,
        "trend": trend,
        "prediction": prediction,
        "confidence": confidence
    }

# =========================
# BOT ONLINE
# =========================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    channel = bot.get_channel(CHANNEL_ID)

    if channel:
        await channel.send(
            "✅ BTC Prediction Bot is now ONLINE."
        )

    market_updates.start()

# =========================
# AUTO MARKET UPDATES
# =========================

@tasks.loop(minutes=1)
async def market_updates():

    global update_minutes

    current_minute = pd.Timestamp.now().minute

    if current_minute % update_minutes != 0:
        return

    channel = bot.get_channel(CHANNEL_ID)

    if not channel:
        print("Channel not found")
        return

    try:

        data = get_prediction()

        color = 0x3498db

        if "UP" in data["prediction"]:
            color = 0x00ff00

        elif "DOWN" in data["prediction"]:
            color = 0xff0000

        embed = discord.Embed(
            title="BTC MARKET PANEL",
            color=color
        )

        embed.add_field(
            name="BTC Price",
            value=f"${data['price']:.2f}",
            inline=False
        )

        embed.add_field(
            name="RSI",
            value=f"{data['rsi']:.2f}",
            inline=False
        )

        embed.add_field(
            name="Trend",
            value=data['trend'],
            inline=False
        )

        embed.add_field(
            name="Prediction",
            value=data['prediction'],
            inline=False
        )

        embed.add_field(
            name="Confidence",
            value=f"{data['confidence']}%",
            inline=False
        )

        embed.set_footer(
            text=f"Updates every {update_minutes} minute(s)"
        )

        await channel.send(embed=embed)

        print("Market update sent")

    except Exception as e:
        print("Error:", e)

# =========================
# SLASH COMMAND: TIMER
# =========================

@bot.slash_command(
    name="settimer",
    description="Change update timer"
)
async def settimer(
    ctx,
    minutes: Option(int, "Minutes between updates")
):

    global update_minutes

    if minutes < 1:
        await ctx.respond(
            "❌ Minimum timer is 1 minute."
        )
        return

    update_minutes = minutes

    await ctx.respond(
        f"✅ Update timer changed to {minutes} minute(s)."
    )

# =========================
# SLASH COMMAND: BTC
# =========================

@bot.slash_command(
    name="btc",
    description="Get instant BTC prediction"
)
async def btc(ctx):

    data = get_prediction()

    color = 0x3498db

    if "UP" in data["prediction"]:
        color = 0x00ff00

    elif "DOWN" in data["prediction"]:
        color = 0xff0000

    embed = discord.Embed(
        title="LIVE BTC PREDICTION",
        color=color
    )

    embed.add_field(
        name="BTC Price",
        value=f"${data['price']:.2f}",
        inline=False
    )

    embed.add_field(
        name="RSI",
        value=f"{data['rsi']:.2f}",
        inline=False
    )

    embed.add_field(
        name="Trend",
        value=data['trend'],
        inline=False
    )

    embed.add_field(
        name="Prediction",
        value=data['prediction'],
        inline=False
    )

    embed.add_field(
        name="Confidence",
        value=f"{data['confidence']}%",
        inline=False
    )

    await ctx.respond(embed=embed)

# =========================
# RUN BOT
# =========================

bot.run(TOKEN)