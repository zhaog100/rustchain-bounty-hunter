#!/usr/bin/env python3
"""RustChain Telegram Bot - Check balance and miner status. Bounty: #2869 (10 RTC)"""
import os, json, urllib.request, urllib.parse, ssl

NODE = os.environ.get("RUSTCHAIN_NODE", "https://rustchain.org")

def api(path):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = 0
    try:
        with urllib.request.urlopen(f"{NODE}{path}", context=ctx, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def handle(text):
    parts = text.strip().split()
    cmd = parts[0].lstrip("/").split("@")[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "balance" and arg:
        d = api(f"/wallet/balance?miner_id={urllib.parse.quote(arg)}")
        if "error" in d: return f"Error: {d['error']}"
        return f"Balance: {d.get('amount_rtc', 0)} RTC"
    elif cmd == "status" and arg:
        d = api(f"/enroll/status?miner_id={urllib.parse.quote(arg)}")
        return json.dumps(d, indent=2)
    elif cmd == "network":
        d = api("/epoch")
        return f"Epoch {d.get('epoch','?')} | Miners: {d.get('enrolled_miners','?')} | Pot: {d.get('epoch_pot','?')} RTC"
    elif cmd == "help":
        return "/balance <id> /status <id> /network /help"
    return "Unknown. Try /help"

if __name__ == "__main__":
    print(handle("/balance zhaog100"))
    print(handle("/network"))
