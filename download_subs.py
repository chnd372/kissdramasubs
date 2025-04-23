import os
import json
import time
import requests
import pandas as pd
from urllib.parse import urlparse
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Load your CSV file
csv_path = "drama_subtitles.csv"
df = pd.read_csv(csv_path)

# Base directory to save subtitles
base_dir = "dramas"
os.makedirs(base_dir, exist_ok=True)

# AES decryption configuration
KEY = b'AmSmZVcH93UQUezi'
IV = b'ReBKWW8cqdjPEnF6'

def decrypt_line(encrypted_line):
    try:
        encrypted_data = base64.b64decode(encrypted_line.strip())
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        print(f"Error decrypting line: {e}")
        return ""

def decrypt_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f_in, open(output_path, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                line = line.strip()
                if not line:
                    f_out.write('\n')
                    continue
                if line.isdigit() or "-->" in line:
                    f_out.write(line + '\n')
                else:
                    decrypted = decrypt_line(line)
                    f_out.write(decrypted + '\n')
        print(f"Decrypted: {output_path}")
        # Delete original encrypted file
        os.remove(input_path)
        print(f"Removed encrypted file: {input_path}")
    except Exception as e:
        print(f"Failed to decrypt file {input_path}: {e}")

# Helper function to download with retry
def download_with_retry(url, path, max_retries=3, delay=2):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded: {path}")
                return True
            else:
                print(f"Attempt {attempt+1}: Failed to download {url} (status {response.status_code})")
        except Exception as e:
            print(f"Attempt {attempt+1}: Error downloading {url}: {e}")
        time.sleep(delay)
    return False

# Process each row in the CSV
for index, row in df.iterrows():
    try:
        drama_title = str(row['Drama Title']).strip().replace("/", "-")
        episode_number = str(row['Episode Number']).strip()
        subtitle_data_json = row['Subtitle Data']

        # Create folders: drama title > episode number
        drama_folder = os.path.join(base_dir, drama_title)
        episode_folder = os.path.join(drama_folder, f"Episode_{episode_number}")
        os.makedirs(episode_folder, exist_ok=True)

        # Parse subtitle data
        subtitle_entries = json.loads(subtitle_data_json)

        for entry in subtitle_entries:
            subtitle_url = entry['src']
            lang_label = entry['label']
            file_extension = os.path.splitext(urlparse(subtitle_url).path)[-1]
            subtitle_filename = f"{lang_label}{file_extension}"
            subtitle_path = os.path.join(episode_folder, subtitle_filename)

            # Download subtitle
            success = download_with_retry(subtitle_url, subtitle_path)
            if not success:
                continue

            # If encrypted, decrypt and delete original
            if file_extension in ['.txt', '.txt1']:
                decrypted_filename = f"{lang_label}.srt"
                decrypted_path = os.path.join(episode_folder, decrypted_filename)
                decrypt_file(subtitle_path, decrypted_path)

            time.sleep(1)  # wait after each subtitle

        time.sleep(2)  # wait after each episode

    except Exception as e:
        print(f"Error processing row {index}: {e}")
