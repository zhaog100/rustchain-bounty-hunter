#!/usr/bin/env python3
"""
RustChain Autonomous Bounty Hunter Agent
=========================================
Scans RustChain bounties on GitHub, evaluates feasibility,
and submits claims or PRs autonomously.

Bounty: Scottcjn/rustchain-bounties#2861 (50 RTC)
Wallet: zhaog100
"""

import json
import os
import subprocess
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

# Configuration
RUSTCHAIN_NODE = os.environ.get("RUSTCHAIN_NODE", "https://rustchain.org")
GITHUB_REPO = "Scottcjn/rustchain-bounties"
WALLET = os.environ.get("RUSTCHAIN_WALLET", "zhaog100")
MIN_RTC = int(os.environ.get("MIN_RTC", "5"))


@dataclass
class Bounty:
    number: int
    title: str
    reward_rtc: int
    url: str
    body: str
    labels: List[str]

    @property
    def is_creative(self) -> bool:
        keywords = ["write", "create", "design", "shanty", "meme", "article", "blog"]
        return any(k in self.title.lower() for k in keywords)

    @property
    def is_coding(self) -> bool:
        keywords = ["build", "implement", "fix", "feat", "code", "agent", "bot", "tool", "action"]
        return any(k in self.title.lower() for k in keywords)

    @property
    def is_security(self) -> bool:
        keywords = ["security", "audit", "red team", "vulnerability", "exploit"]
        return any(k in self.title.lower() for k in keywords)

    @property
    def difficulty(self) -> str:
        if self.reward_rtc >= 50:
            return "hard"
        elif self.reward_rtc >= 15:
            return "medium"
        return "easy"


def run_gh(args: List[str]) -> Optional[str]:
    """Run gh CLI command and return output."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def check_node_health() -> Dict:
    """Verify RustChain node is reachable."""
    try:
        result = subprocess.run(
            ["curl", "-sk", f"{RUSTCHAIN_NODE}/health"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return {"ok": False}


def check_balance() -> float:
    """Check wallet balance."""
    try:
        result = subprocess.run(
            ["curl", "-sk", f"{RUSTCHAIN_NODE}/wallet/balance?miner_id={WALLET}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("amount_rtc", 0)
    except Exception:
        pass
    return 0.0


def scan_bounties() -> List[Bounty]:
    """Scan open bounties from GitHub."""
    output = run_gh([
        "issue", "list",
        "--repo", GITHUB_REPO,
        "--state", "open",
        "--limit", "100",
        "--json", "number,title,body,labels,url"
    ])
    if not output:
        return []

    issues = json.loads(output)
    bounties = []

    for issue in issues:
        title = issue.get("title", "")
        body = issue.get("body", "") or ""
        # Extract RTC amount from title
        import re
        rtc_match = re.search(r'(\d+)\s*RTC', title, re.IGNORECASE)
        if rtc_match:
            reward = int(rtc_match.group(1))
            if reward >= MIN_RTC:
                bounties.append(Bounty(
                    number=issue["number"],
                    title=title,
                    reward_rtc=reward,
                    url=issue.get("url", ""),
                    body=body[:500],
                    labels=[l.get("name", "") for l in issue.get("labels", [])]
                ))

    return sorted(bounties, key=lambda b: b.reward_rtc, reverse=True)


def evaluate_bounty(bounty: Bounty) -> Dict:
    """Evaluate if we can complete this bounty."""
    score = 0
    reasons = []

    # Creative tasks are easy
    if bounty.is_creative:
        score += 30
        reasons.append("creative task (low barrier)")

    # Security tasks match our expertise
    if bounty.is_security:
        score += 40
        reasons.append("security expertise match")

    # Coding tasks we can handle
    if bounty.is_coding and bounty.difficulty != "hard":
        score += 20
        reasons.append("coding task within capability")

    # Higher reward = higher priority
    score += min(bounty.reward_rtc, 30)
    reasons.append(f"{bounty.reward_rtc} RTC reward")

    return {
        "bounty": f"#{bounty.number}",
        "score": score,
        "recommendation": "DO" if score >= 40 else "SKIP",
        "reasons": reasons,
        "type": "security" if bounty.is_security else "creative" if bounty.is_creative else "coding"
    }


def submit_claim(bounty: Bounty, claim_body: str) -> bool:
    """Submit a bounty claim comment."""
    result = run_gh([
        "issue", "comment", str(bounty.number),
        "--repo", GITHUB_REPO,
        "--body", claim_body
    ])
    return result is not None


def main():
    """Main agent loop."""
    print("🌾 RustChain Bounty Hunter Agent v1.0")
    print(f"   Node: {RUSTCHAIN_NODE}")
    print(f"   Wallet: {WALLET}")
    print()

    # 1. Health check
    print("1. Checking node health...")
    health = check_node_health()
    if not health.get("ok"):
        print("   ❌ Node unreachable!")
        return
    print(f"   ✅ Node OK (v{health.get('version', '?')})")

    # 2. Check balance
    balance = check_balance()
    print(f"2. Wallet balance: {balance} RTC")

    # 3. Scan bounties
    print("3. Scanning bounties...")
    bounties = scan_bounties()
    print(f"   Found {len(bounties)} bounties (≥{MIN_RTC} RTC)")

    # 4. Evaluate
    print("\n4. Evaluation:")
    evaluations = []
    for b in bounties[:20]:
        ev = evaluate_bounty(b)
        evaluations.append(ev)
        icon = "✅" if ev["recommendation"] == "DO" else "⏭️"
        print(f"   {icon} #{b.number} ({b.reward_rtc} RTC) "
              f"[{ev['type']}] score={ev['score']} — {', '.join(ev['reasons'][:2])}")

    # 5. Summary
    do_list = [e for e in evaluations if e["recommendation"] == "DO"]
    print(f"\n📊 Summary: {len(do_list)}/{len(evaluations)} bounties recommended")
    print(f"💰 Potential: {sum(b.reward_rtc for b in bounties[:20])} RTC")

    return {
        "health": health,
        "balance": balance,
        "bounties_found": len(bounties),
        "recommended": len(do_list)
    }


if __name__ == "__main__":
    main()
