"""
Roblox Ban Queue Server
========================
A simple server that sits between your Discord bot and Roblox Studio.

- Discord bot posts bans/unbans here
- Roblox Studio script polls here for pending bans/unbans

Run locally:  python server.py
Deploy on:    Render.com (free tier)
"""

import os
import json
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

SHARED_SECRET = "EMAdabest"  # make up any password
                                                   # must match the plugin

# ──────────────────────────────────────────────────────────────────────────────

BANS_FILE   = "bans.json"
UNBANS_FILE = "unbans.json"


def load(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)


def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


def next_id(items):
    if not items:
        return 1
    return max(i["id"] for i in items) + 1


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── BANS ──────────────────────────────────────────────────────────────────────

@app.route("/bans", methods=["POST"])
def create_ban():
    data = request.get_json()
    if not data or data.get("secret") != SHARED_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    roblox_user_id = data.get("robloxUserId")
    roblox_username = data.get("robloxUsername")
    if not roblox_user_id or not roblox_username:
        return jsonify({"error": "robloxUserId and robloxUsername are required"}), 400

    bans = load(BANS_FILE)
    ban = {
        "id": next_id(bans),
        "robloxUserId": roblox_user_id,
        "robloxUsername": roblox_username,
        "status": "pending",
        "createdAt": now(),
        "completedAt": None,
    }
    bans.append(ban)
    save(BANS_FILE, bans)
    print(f"[BanQueue] Queued ban for {roblox_username}")
    return jsonify(ban), 201


@app.route("/bans/pending", methods=["GET"])
def pending_bans():
    bans = load(BANS_FILE)
    return jsonify({"bans": [b for b in bans if b["status"] == "pending"]})


@app.route("/bans/<int:ban_id>/complete", methods=["PATCH"])
def complete_ban(ban_id):
    bans = load(BANS_FILE)
    for ban in bans:
        if ban["id"] == ban_id:
            ban["status"] = "completed"
            ban["completedAt"] = now()
            save(BANS_FILE, bans)
            print(f"[BanQueue] Ban {ban_id} completed ({ban['robloxUsername']})")
            return jsonify(ban)
    return jsonify({"error": "Ban not found"}), 404


# ── UNBANS ────────────────────────────────────────────────────────────────────

@app.route("/unbans", methods=["POST"])
def create_unban():
    data = request.get_json()
    if not data or data.get("secret") != SHARED_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    roblox_user_id = data.get("robloxUserId")
    roblox_username = data.get("robloxUsername")
    if not roblox_user_id or not roblox_username:
        return jsonify({"error": "robloxUserId and robloxUsername are required"}), 400

    unbans = load(UNBANS_FILE)
    unban = {
        "id": next_id(unbans),
        "robloxUserId": roblox_user_id,
        "robloxUsername": roblox_username,
        "status": "pending",
        "createdAt": now(),
        "completedAt": None,
    }
    unbans.append(unban)
    save(UNBANS_FILE, unbans)
    print(f"[BanQueue] Queued unban for {roblox_username}")
    return jsonify(unban), 201


@app.route("/unbans/pending", methods=["GET"])
def pending_unbans():
    unbans = load(UNBANS_FILE)
    return jsonify({"unbans": [u for u in unbans if u["status"] == "pending"]})


@app.route("/unbans/<int:unban_id>/complete", methods=["PATCH"])
def complete_unban(unban_id):
    unbans = load(UNBANS_FILE)
    for unban in unbans:
        if unban["id"] == unban_id:
            unban["status"] = "completed"
            unban["completedAt"] = now()
            save(UNBANS_FILE, unbans)
            print(f"[BanQueue] Unban {unban_id} completed ({unban['robloxUsername']})")
            return jsonify(unban)
    return jsonify({"error": "Unban not found"}), 404


# ── KICKS ────────────────────────────────────────────────────────────────────

@app.route("/kicks", methods=["POST"])
def create_kick():
    data = request.get_json()
    if not data or data.get("secret") != SHARED_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    roblox_user_id = data.get("robloxUserId")
    roblox_username = data.get("robloxUsername")
    reason = data.get("reason", "Kicked by server moderation.")
    if not roblox_user_id or not roblox_username:
        return jsonify({"error": "robloxUserId and robloxUsername are required"}), 400

    kicks = load("kicks.json")
    kick = {
        "id": next_id(kicks),
        "robloxUserId": roblox_user_id,
        "robloxUsername": roblox_username,
        "reason": reason,
        "status": "pending",
        "createdAt": now(),
        "completedAt": None,
    }
    kicks.append(kick)
    save("kicks.json", kicks)
    print(f"[BanQueue] Queued kick for {roblox_username}")
    return jsonify(kick), 201


@app.route("/kicks/pending", methods=["GET"])
def pending_kicks():
    kicks = load("kicks.json")
    return jsonify({"kicks": [k for k in kicks if k["status"] == "pending"]})


@app.route("/kicks/<int:kick_id>/complete", methods=["PATCH"])
def complete_kick(kick_id):
    kicks = load("kicks.json")
    for kick in kicks:
        if kick["id"] == kick_id:
            kick["status"] = "completed"
            kick["completedAt"] = now()
            save("kicks.json", kicks)
            print(f"[BanQueue] Kick {kick_id} completed ({kick['robloxUsername']})")
            return jsonify(kick)
    return jsonify({"error": "Kick not found"}), 404


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[BanQueue] Server starting on port {port}")
    app.run(host="0.0.0.0", port=port)
