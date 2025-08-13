"""
CREATE A BOT INSTANCE FROM DISCORD DEV PAGE AND ENABLE INTENTS FOR THIS TO WORK. 
CBA ABOUT RATELIMIT SO HAVE FUN!

"""



import requests
import threading
import time
import os
import sys

os.system('cls' if os.name == 'nt' else 'clear')
os.makedirs('Scraped', exist_ok=True)

os.system(f'cls & mode 85,20 & title [DISCORD.GG/WRD] - PLAYEDYABTCH')

token   = input("$-> Bot Token: ").strip()
guildId = input("$-> Guild ID: ").strip()
message = input("$-> DM message to send: ").strip()

headers = {
    "Authorization": f"Bot {token}",
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (dm-all/1.0)"
}

def get_self_id():
    r = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
    if r.status_code != 200:
        print("[!] Token check failed:", r.status_code, r.text); sys.exit(1)
    return r.json()["id"]

ME_ID = get_self_id()

def scrape_members():
    print("[!] Scraping members...")
    all_ids = []
    after = None
    while True:
        params = {"limit": 1000}
        if after: params["after"] = after
        url = f"https://discord.com/api/v10/guilds/{guildId}/members"
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 403:
            print("[!] 403 Forbidden fetching members. Enable 'Server Members Intent' in the Developer Portal.")
            sys.exit(1)
        if r.status_code != 200:
            print(f"[!] Failed to fetch members (status {r.status_code})\n{r.text}")
            sys.exit(1)
        batch = r.json()
        if not batch: break
        for m in batch:
            uid = m["user"]["id"]
            if uid != ME_ID:  
                all_ids.append(uid)
        after = batch[-1]["user"]["id"]
        if len(batch) < 1000: break

    with open("Scraped/members.txt", "w") as f:
        for uid in all_ids:
            f.write(uid + "\n")
    print(f"[+] Scraped {len(all_ids)} members into Scraped/members.txt\n")

def open_dm(user_id):
    payload = {"recipient_id": user_id}
    while True:
        r = requests.post("https://discord.com/api/v10/users/@me/channels", headers=headers, json=payload)
        if r.status_code in (200, 201):
            return r.json()["id"]
        if r.status_code == 429:
            time.sleep(float(r.json().get("retry_after", 1)))
            continue
        return None

def send_dm(channel_id, content):
    payload = {"content": content}
    while True:
        r = requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages", headers=headers, json=payload)
        if r.status_code in (200, 201):
            return True
        if r.status_code == 429:
            time.sleep(float(r.json().get("retry_after", 1)))
            continue
        return False

MAX_THREADS = 20
sem = threading.BoundedSemaphore(MAX_THREADS)

success = 0
failed  = 0
lock = threading.Lock()

def dm_user(user_id):
    global success, failed
    with sem:
        uid = user_id.strip()
        if not uid: 
            return
        ch_id = open_dm(uid)
        if not ch_id:
            with lock:
                failed += 1
                print(f"[!] Failed to open DM with {uid}")
            return
        ok = send_dm(ch_id, message)
        with lock:
            if ok:
                success += 1
                print(f"[+] DM sent to {uid}")
            else:
                failed += 1
                print(f"[!] Failed to send DM to {uid}")

def mass_dm():
    try:
        with open("Scraped/members.txt", "r") as f:
            ids = [x.strip() for x in f if x.strip()]
    except FileNotFoundError:
        print("[!] Scraped/members.txt not found. Run scraper first.")
        sys.exit(1)

    print(f"[!] Launching DM threads for {len(ids)} user(s)...\n")
    threads = []
    for uid in ids:
        t = threading.Thread(target=dm_user, args=(uid,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    print(f"\n[SUCCESS] Done. Sent: {success} | Failed: {failed}")

if __name__ == "__main__":
    scrape_members()
    mass_dm()
