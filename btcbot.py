import os
import discord
from discord.ext import tasks
import ccxt

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1509736189798650079

exchange = ccxt.binance()

intents = discord.Intents.default()
client = discord.Client(intents=intents)


def simple_signal():
    ticker = exchange.fetch_ticker('BTC/USDT')

    price = ticker['last']
    change = ticker['percentage']

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
        "confidence": int(confidence)
    }


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    btc_loop.start()


@tasks.loop(minutes=30)
async def btc_loop():

    channel = client.get_channel(CHANNEL_ID)

    try:
        data = simple_signal()

        embed = discord.Embed(
            title="₿ BTC SIGNAL",
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

        await channel.send(embed=embed)

        print("Signal sent")

    except Exception as e:
        print("Error:", e)


client.run(TOKEN)
