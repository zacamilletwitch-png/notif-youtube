"""Vérifie le flux RSS d'une chaîne YouTube et annonce les nouvelles vidéos sur Discord."""
import json
import os
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = os.environ["YOUTUBE_CHANNEL_ID"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
PING = os.environ.get("PING") or "@everyone"
STATE_FILE = "last_video.txt"

NS = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def fetch_videos():
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    videos = []
    for entry in root.findall("atom:entry", NS):
        videos.append({
            "id": entry.find("yt:videoId", NS).text,
            "title": entry.find("atom:title", NS).text,
            "url": entry.find("atom:link", NS).attrib["href"],
        })
    return videos


def post_to_discord(video):
    payload = {
        "content": f"{PING} 🎬 **Nouvelle vidéo !**\n**{video['title']}**\n{video['url']}",
        "allowed_mentions": {"parse": ["everyone", "roles"]},
    }
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "yt-discord-notif"},
    )
    urllib.request.urlopen(req, timeout=30)


def main():
    videos = fetch_videos()
    if not videos:
        return

    last_id = open(STATE_FILE).read().strip() if os.path.exists(STATE_FILE) else None

    if last_id is None:
        print(f"Initialisation sur : {videos[0]['title']}")
    else:
        new = []
        for v in videos:
            if v["id"] == last_id:
                break
            new.append(v)
        for v in reversed(new):
            print(f"Annonce : {v['title']}")
            post_to_discord(v)

    with open(STATE_FILE, "w") as f:
        f.write(videos[0]["id"])


if __name__ == "__main__":
    main()
