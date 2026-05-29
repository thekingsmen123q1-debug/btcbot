import os
import discord
from discord.ext import tasks
import ccxt
import pandas as pd
from ta.momentum import RSIIndicator

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1509736189798650079

exchange = ccxt.binance()

intents = discord.Intents.default()
client = discord.Client(intents=intents)


def analyze_timeframe(symbol, timeframe, limit=100):

    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    df = pd.DataFrame(candles, columns=[
        'timestamp','open','high','low','close','volume'
    ])

    df['close'] = df['close'].astype(float)

    rsi = RSIIndicator(df['close'], window=14)
    df['rsi'] = rsi.rsi()

    df['ema_fast'] = df['close'].ewm(span=9).mean()
    df['ema_slow'] = df['close'].ewm(span=21).mean()

    latest = df.iloc[-1]

    trend = 0

    if latest['ema_fast'] > latest['ema_slow']:
        trend += 1
    else:
        trend -= 1

    if latest['rsi'] < 45:
        trend += 0.5
    elif latest['rsi'] > 55:
        trend -= 0.5

    return trend, latest['rsi'], float(latest['close']), df

def get_prediction():

    t1, rsi1, price, df1 = analyze_timeframe('BTC/USDT', '1m')
    t2, rsi2, _, df2 = analyze_timeframe('BTC/USDT', '5m')
    t3, rsi3, _, df3 = analyze_timeframe('BTC/USDT', '1h')

    total_score = (t1 * 0.5) + (t2 * 1.5) + (t3 * 2.5)

    direction = "NEUTRAL ⏳"
    confidence = 50

    if total_score > 1.5:
        direction = "UP 🟢"
        confidence = min(95, 55 + total_score * 10)

    elif total_score < -1.5:
        direction = "DOWN 🔴"
        confidence = min(95, 55 + abs(total_score) * 10)

    volatility = df1['close'].pct_change().abs().rolling(10).mean().iloc[-1]

    reversal_minutes = int(8 + (1 / (volatility + 0.0001)) * 2)

    return {
        "price": price,
        "rsi": rsi1,
        "direction": direction,
        "confidence": int(confidence),
        "reversal_minutes": reversal_minutes
    }

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    btc_loop.start()


@tasks.loop(minutes=30)
async def btc_loop():

    channel = client.get_channel(CHANNEL_ID)

    try:
        data = get_prediction()

        embed = discord.Embed(
            title="₿ BTC MARKET SIGNAL",
            color=0x00ff00 if "UP" in data["direction"] else 0xff0000
        )

        embed.add_field(
            name="Signal",
            value=f"{data['direction']}\n📊 Confidence: {data['confidence']}%",
            inline=False
        )

        embed.add_field(
            name="Price",
            value=f"${data['price']:.2f}",
            inline=True
        )

        embed.add_field(
            name="Reversal Estimate",
            value=f"⏳ ~{data['reversal_minutes']} minutes",
            inline=False
        )

        embed.set_footer(text="Multi-timeframe trend model (educational)")

        await channel.send(embed=embed)

        print("Signal sent")

    except Exception as e:
        print("Error:", e)


client.run(TOKEN)
