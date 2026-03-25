"""
Roblox Ban Queue Server
========================
A simple server that sits between your Discord bot and Roblox Studio.

- Discord bot posts bans here
- Roblox Studio script polls here for pending bans

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
                                                   # must match the plugin + studio script

# ──────────────────────────────────────────────────────────────────────────────

DB_FILE = "bans.json"


def load_bans():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_bans(bans):
    with open(DB_FILE, "w") as f:
        json.dump(bans, f, indent=2)


def next_id(bans):
    if not bans:
        return 1
    return max(b["id"] for b in bans) + 1


# POST /bans — Discord bot queues a ban
@app.route("/bans", methods=["POST"])
def create_ban():
    data = request.get_json()

    if not data or data.get("secret") != SHARED_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    roblox_user_id = data.get("robloxUserId")
    roblox_username = data.get("robloxUsername")

    if not roblox_user_id or not roblox_username:
        return jsonify({"error": "robloxUserId and robloxUsername are required"}), 400

    bans = load_bans()
    ban = {
        "id": next_id(bans),
        "robloxUserId": roblox_user_id,
        "robloxUsername": roblox_username,
        "status": "pending",
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "completedAt": None,
    }
    bans.append(ban)
    save_bans(bans)

    print(f"[BanQueue] Queued ban for {roblox_username} (ID: {roblox_user_id})")
    return jsonify(ban), 201


# GET /bans/pending — Roblox Studio polls for pending bans
@app.route("/bans/pending", methods=["GET"])
def pending_bans():
    bans = load_bans()
    pending = [b for b in bans if b["status"] == "pending"]
    return jsonify({"bans": pending})


# PATCH /bans/<id>/complete — Roblox Studio marks a ban as done
@app.route("/bans/<int:ban_id>/complete", methods=["PATCH"])
def complete_ban(ban_id):
    bans = load_bans()
    for ban in bans:
        if ban["id"] == ban_id:
            ban["status"] = "completed"
            ban["completedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            save_bans(bans)
            print(f"[BanQueue] Ban {ban_id} marked complete ({ban['robloxUsername']})")
            return jsonify(ban)
    return jsonify({"error": "Ban not found"}), 404


# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[BanQueue] Server starting on port {port}")
    app.run(host="0.0.0.0", port=port)
