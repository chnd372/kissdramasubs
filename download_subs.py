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

# AES decryption configuration - Multiple keys and IVs for different encryption types
# Original key/iv pair
KEY1 = b'AmSmZVcH93UQUezi'
IV1 = b'ReBKWW8cqdjPEnF6'

# Additional key/iv pairs from KissKhClient.py
KEY2 = b'8056483646328763'
IV2 = b'6852612370185273'

# Default encryption key/iv
KEY3 = b'sWODXX04QRTkHdlZ'
IV3 = b'8pwhapJeC4hrS9hO'

def is_encrypted(line):
    """
    Check if a line looks like it's base64 encoded (encrypted)
    """
    # Base64 strings typically only contain these characters
    base64_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    
    # If the line is very short, it's likely not encrypted
    if len(line) < 10:
        return False
        
    # Check if the line only contains base64 characters
    return all(char in base64_chars for char in line.strip())

def decrypt_line(encrypted_line, file_ext):
    """
    Decrypt a single line using the appropriate key/iv based on file extension
    """
    try:
        encrypted_data = base64.b64decode(encrypted_line.strip())
        
        # Select appropriate key/iv based on file extension
        if file_ext == '.txt':
            cipher = AES.new(KEY2, AES.MODE_CBC, IV2)
        elif file_ext == '.txt1':
            cipher = AES.new(KEY1, AES.MODE_CBC, IV1)
        elif file_ext in ['.txt2', '.txt3']:
            cipher = AES.new(KEY3, AES.MODE_CBC, IV3)
        else:
            # Default to KEY3/IV3 for unknown extensions
            cipher = AES.new(KEY3, AES.MODE_CBC, IV3)
            
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        print(f"Error decrypting line with {file_ext} key/iv: {e}")
        # If first attempt fails, try with other keys in sequence
        try_alternate_keys = True
        if try_alternate_keys:
            try:
                alternate_keys = [
                    (KEY1, IV1, "KEY1/IV1"),
                    (KEY2, IV2, "KEY2/IV2"),
                    (KEY3, IV3, "KEY3/IV3")
                ]
                for key, iv, key_name in alternate_keys:
                    try:
                        cipher = AES.new(key, AES.MODE_CBC, iv)
                        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
                        print(f"Successfully decrypted with alternate {key_name}")
                        return decrypted_data.decode('utf-8')
                    except:
                        continue
            except:
                pass
        return encrypted_line  # Return original line if decryption fails

def check_if_file_encrypted(file_path):
    """
    Check if the file appears to be encrypted by sampling some lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Skip empty lines, timestamps, and subtitle numbers
        content_lines = [line.strip() for line in lines 
                        if line.strip() and not line.strip().isdigit() and "-->" not in line]
        
        if not content_lines:
            return False
            
        # Check a sample of lines (up to 10)
        sample_size = min(10, len(content_lines))
        sample_lines = content_lines[:sample_size]
        
        # If most lines appear to be encrypted, consider the file encrypted
        encrypted_count = sum(1 for line in sample_lines if is_encrypted(line))
        return encrypted_count > (sample_size // 2)
    except Exception as e:
        print(f"Error checking if file is encrypted: {e}")
        # Default to assuming it's encrypted if we can't check
        return True

def decrypt_file(input_path, output_path):
    """
    Decrypt file with appropriate key/iv based on file extension
    """
    try:
        # Check if the file is actually encrypted
        if not check_if_file_encrypted(input_path):
            print(f"File {input_path} doesn't appear to be encrypted, copying as is")
            # If not encrypted, just copy the file to output with .srt extension
            with open(input_path, 'r', encoding='utf-8') as f_in, open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write(f_in.read())
            # Delete original file
            os.remove(input_path)
            print(f"Copied and renamed: {output_path}")
            return
        
        # Get file extension for key/iv selection
        file_ext = os.path.splitext(input_path)[1].lower()
        
        print(f"Decrypting {input_path} with {file_ext} key/iv pair")
        with open(input_path, 'r', encoding='utf-8') as f_in, open(output_path, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                line = line.strip()
                if not line:
                    f_out.write('\n')
                    continue
                if line.isdigit() or "-->" in line:
                    f_out.write(line + '\n')
                else:
                    # Only decrypt lines that appear to be encrypted
                    if is_encrypted(line):
                        decrypted = decrypt_line(line, file_ext)
                        f_out.write(decrypted + '\n')
                    else:
                        f_out.write(line + '\n')
        print(f"Decrypted: {output_path}")
        # Delete original encrypted file
        os.remove(input_path)
        print(f"Removed original file: {input_path}")
    except Exception as e:
        print(f"Failed to process file {input_path}: {e}")

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

            # If potentially encrypted, try to decrypt and delete original
            if file_extension in ['.txt', '.txt1', '.txt2', '.txt3', '.srt']:
                decrypted_filename = f"{lang_label}.srt"
                decrypted_path = os.path.join(episode_folder, decrypted_filename)
                decrypt_file(subtitle_path, decrypted_path)
            else:
                # For unknown extensions, just keep the file as is
                print(f"Unknown file extension: {file_extension}, keeping original file")

            time.sleep(1)  # wait after each subtitle

        time.sleep(2)  # wait after each episode

    except Exception as e:
        print(f"Error processing row {index}: {e}")

# Clean up CSV files after processing
print("\nCleaning up CSV files...")
csv_files_to_delete = ["drama_details.csv", "drama_subtitles.csv"]
for csv_file in csv_files_to_delete:
    try:
        if os.path.exists(csv_file):
            os.remove(csv_file)
            print(f"Deleted: {csv_file}")
        else:
            print(f"File not found: {csv_file}")
    except Exception as e:
        print(f"Error deleting {csv_file}: {e}")

print("\nProcessing complete!")