
import ccxt
import time
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timezone

# --- Configuration ---
COINS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT", "PEPE/USDT"]
TIMEFRAME = "1m"
BALANCE = 10000.0  # Simulated USDT
POSITION_SIZE = 50
TRADE_LOG = []
LIVE_MODE = False
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1370514358961963039/RlCTRbvNkcmVDXOnRvWF795M9wriWzwj88EG_LbISoZQEK-p_9WZ_3T7d7hs89YNwKQr"

# --- Initialize Exchange ---
exchange = ccxt.binance()

# --- Trade Simulation ---
def fetch_ohlcv(symbol, timeframe="1m", limit=100):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return []

def simulate_trade(symbol, data):
    open_price = data[-2][1]
    close_price = data[-1][4]
    direction = "LONG" if close_price > open_price else "SHORT"
    result = "WIN" if direction == "LONG" and close_price > open_price else "LOSS"
    profit = POSITION_SIZE * (0.003 if result == "WIN" else -0.002)
    timestamp = datetime.now(timezone.utc).isoformat()

    trade = {
        "timestamp": timestamp,
        "symbol": symbol,
        "direction": direction,
        "entry_price": open_price,
        "exit_price": close_price,
        "pnl": profit,
        "result": result
    }
    TRADE_LOG.append(trade)
    return profit, trade

# --- Graph Rendering ---
def generate_balance_graph():
    timestamps = [t['timestamp'] for t in TRADE_LOG]
    balances = [10000.0 + sum(t['pnl'] for t in TRADE_LOG[:i+1]) for i in range(len(TRADE_LOG))]
    plt.figure(figsize=(10, 4))
    plt.plot(timestamps, balances, marker='o')
    plt.title("EchoBot Simulated Balance Over Time")
    plt.xlabel("Time")
    plt.ylabel("Balance (USDT)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    graph_path = "/tmp/balance_graph.png"
    plt.savefig(graph_path)
    plt.close()
    return graph_path

# --- Discord Alerts ---
def send_discord_alert(trades, current_balance):
    message = "**📡 EchoBot Simulation Cycle**\n"
    for trade in trades:
        message += (
            f"**{trade['symbol']}** | {trade['direction']} | "
            f"Entry: `{trade['entry_price']}` → Exit: `{trade['exit_price']}`\n"
            f"PnL: `{trade['pnl']:.2f}` | Result: **{trade['result']}**\n\n"
        )
    message += f"**New Balance:** `{current_balance:.2f} USDT`"

    graph_file = generate_balance_graph()
    with open(graph_file, 'rb') as f:
        files = {'file': ('balance_graph.png', f)}
        data = {"content": message}
        response = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files)
        if response.status_code != 204:
            print(f"Failed to send Discord alert: {response.status_code}")

# --- Main Simulation Loop ---
def run_simulation():
    global BALANCE
    print(f"Starting EchoBot simulation with {BALANCE} USDT...")
    while True:
        trades_this_round = []
        for coin in COINS:
            data = fetch_ohlcv(coin, TIMEFRAME)
            if len(data) > 2:
                pnl, trade = simulate_trade(coin, data)
                BALANCE += pnl
                trades_this_round.append(trade)
                print(f"{coin} | PnL: {pnl:.2f} | New Balance: {BALANCE:.2f}")
        if trades_this_round:
            send_discord_alert(trades_this_round, BALANCE)
        time.sleep(60)

if __name__ == "__main__":
    run_simulation()
