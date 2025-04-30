#!/usr/bin/env python3
import os
import sys
import json
import time
import base64
import requests
import pandas as pd
import re
import argparse
from urllib.parse import urlparse
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

DRAMA_DETAILS_CSV = "drama_details.csv"
DRAMA_SUBTITLES_CSV = "drama_subtitles.csv"
OUTPUT_DIR = "dramas"

KEY1 = b'AmSmZVcH93UQUezi'
IV1 = b'ReBKWW8cqdjPEnF6'
KEY2 = b'8056483646328763'
IV2 = b'6852612370185273'
KEY3 = b'sWODXX04QRTkHdlZ'
IV3 = b'8pwhapJeC4hrS9hO'

def current_time():
    return datetime.now().strftime("%H:%M:%S")

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '-', name)

def is_encrypted(line):
    return len(line) > 10 and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in line.strip())

def decrypt_line(encrypted_line, file_ext):
    try:
        encrypted_data = base64.b64decode(encrypted_line.strip())
        key_iv = {
            ".txt": (KEY2, IV2),
            ".txt1": (KEY1, IV1),
            ".txt2": (KEY3, IV3),
            ".txt3": (KEY3, IV3),
        }.get(file_ext, (KEY3, IV3))
        cipher = AES.new(*key_iv, AES.MODE_CBC)
        return unpad(cipher.decrypt(encrypted_data), AES.block_size).decode("utf-8")
    except:
        for key, iv in [(KEY1, IV1), (KEY2, IV2), (KEY3, IV3)]:
            try:
                cipher = AES.new(key, AES.MODE_CBC, iv)
                return unpad(cipher.decrypt(encrypted_data), AES.block_size).decode("utf-8")
            except:
                continue
    return encrypted_line

def fetch_drama_data(start_id, end_id):
    all_data = []
    for drama_id in tqdm(range(start_id, end_id + 1), desc="Step 1: Drama metadata"):
        try:
            res = requests.get(f"https://kisskh.ovh/api/DramaList/Drama/{drama_id}", timeout=30)
            if res.status_code != 200:
                continue
            data = res.json()
            episodes = data.get("episodes", [])
            episode_details = "; ".join(f"Episode {ep.get('number')} (ID: {ep.get('id')}, Subtitles: {ep.get('sub')})" for ep in episodes)
            all_data.append({
                "Show ID": data.get("id"),
                "Title": data.get("title"),
                "Episode Details": episode_details.strip()
            })
        except Exception:
            continue
    pd.DataFrame(all_data).to_csv(DRAMA_DETAILS_CSV, index=False, encoding="utf-8-sig")
    print(f"[INFO] Saved drama metadata to {DRAMA_DETAILS_CSV} [Time : {current_time()}]")
    return all_data

def parse_episode_details(details):
    pattern = r"Episode\s+(\d+(?:\.\d+)?)\s+\(ID:\s*(\d+),\s*Subtitles:\s*(\d+)\)"
    return [{"number": int(float(m.group(1))), "id": m.group(2)} for m in re.finditer(pattern, details)]

def fetch_kkey_and_subs_task(show_id, title, ep_num, ep_id):
    drama_link = f"https://kisskh.ovh/Drama/a/Episode-{ep_num}?id={show_id}&ep={ep_id}"
    kkey = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        def handle_response(response):
            nonlocal kkey
            if f"/api/Sub/{ep_id}?kkey=" in response.url:
                match = re.search(r"kkey=([^&]+)", response.url)
                if match:
                    kkey = match.group(1)
        page.on("response", handle_response)
        page.goto(drama_link, timeout=30000, wait_until="networkidle")
        for _ in range(10):
            if kkey:
                break
            time.sleep(1)
        browser.close()
    if not kkey:
        return None
    sub_link = f"https://kisskh.ovh/api/Sub/{ep_id}?kkey={kkey}"
    resp = requests.get(sub_link, headers={'Referer': drama_link})
    return resp.json() if resp.status_code == 200 else None

def download_and_decrypt_subs(title, ep_num, sub_entries, langs):
    folder = os.path.join(OUTPUT_DIR, sanitize_filename(title), f"Episode_{ep_num}")
    os.makedirs(folder, exist_ok=True)
    for entry in sub_entries:
        if langs and entry.get("land") not in langs:
            continue
        url = entry["src"]
        label = entry["label"]
        ext = os.path.splitext(urlparse(url).path)[-1].lower()
        raw_file = os.path.join(folder, f"{label}{ext}")
        final_file = os.path.join(folder, f"{label}.srt")
        time.sleep(1)
        try:
            r = requests.get(url, timeout=10)
            if not r.ok:
                continue
            with open(raw_file, "wb") as f:
                f.write(r.content)
            if ext == ".srt":
                # Already decrypted
                os.rename(raw_file, final_file)
            else:
                with open(raw_file, "r", encoding="utf-8") as f, open(final_file, "w", encoding="utf-8") as out:
                    for line in f:
                        if is_encrypted(line):
                            out.write(decrypt_line(line, ext) + "\n")
                        else:
                            out.write(line)
                os.remove(raw_file)
        except Exception as e:
            print(f"[WARN] Failed to process {label}: {url}")

def main():
    parser = argparse.ArgumentParser(description="KissKH Subtitle Downloader CLI")
    parser.add_argument("start_id", nargs="?", type=int)
    parser.add_argument("-E", "--end-id", type=int)
    parser.add_argument("-e", "--ep", type=str, help="Comma-separated episodes to download")
    parser.add_argument("-t", "--threads", type=int, default=6)
    parser.add_argument("-l", "--langs", type=str, help="Comma-separated language codes to keep (en,hi,etc)")
    parser.add_argument("-c", "--csv", choices=["keep", "delete"], default="keep")
    parser.add_argument("-m", "--meta-skip", action="store_true")
    args = parser.parse_args()

    
    # Normalize and sort episode list
    if args.ep:
        selected_eps = sorted(set(map(int, re.split(r"[,\s]+", args.ep.strip()))))
    else:
        selected_eps = None

    # Normalize and sanitize language codes (en.hi → en,hi → {"en", "hi"})
    if args.langs:
        langs = set(re.split(r"[,.\s]+", args.langs.strip()))
    else:
        langs = None
    start_id = args.start_id
    end_id = args.end_id if args.end_id else start_id

    if not args.meta_skip:
        drama_data = fetch_drama_data(start_id, end_id)
    else:
        print("[INFO] Using Existing CSV meta files by user")
        drama_data = pd.read_csv(DRAMA_DETAILS_CSV).to_dict("records")

    subtitle_data = []
    futures = {}
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        for drama in drama_data:
            show_id = drama["Show ID"]
            title = drama["Title"]
            episodes = parse_episode_details(drama["Episode Details"])
            for ep in episodes:
                if selected_eps and ep["number"] not in selected_eps:
                    continue
                future = executor.submit(fetch_kkey_and_subs_task, show_id, title, ep["number"], ep["id"])
                futures[future] = (title, ep["number"])

        for future in tqdm(as_completed(futures), total=len(futures), desc="Step 2: Subtitle Metadata"):
            result = future.result()
            title, ep_num = futures[future]
            if result:
                subtitle_data.append((title, ep_num, result))


    pd.DataFrame([{"Title": t, "Episode Number": ep, "Subtitle Data": json.dumps(subs)} for t, ep, subs in subtitle_data]).to_csv(DRAMA_SUBTITLES_CSV, index=False, encoding="utf-8-sig")
    #print(f"Step 2: Subtitle Metadata: 100%|{'█'*24} {len(subtitle_data)}/{len(subtitle_data)} [00:00<00:00]")
    print(f"[INFO] Saved subtitle metadata to {DRAMA_SUBTITLES_CSV} [Time : {current_time()}]")

    for title, ep, subs in tqdm(sorted(subtitle_data, key=lambda x: (sanitize_filename(x[0]), x[1])), desc="Step 3: Download + Decrypt"):
        download_and_decrypt_subs(title, ep, subs, langs)

    if args.csv == "delete":
        try:
            os.remove(DRAMA_DETAILS_CSV)
            os.remove(DRAMA_SUBTITLES_CSV)
        except:
            pass
    else:
        print(f"[INFO] CSV meta files keep by user")

    print(f"[INFO] All Subtitles Download Completed [Time : {current_time()}]")

if __name__ == "__main__":
    main()
