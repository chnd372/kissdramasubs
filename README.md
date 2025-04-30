# KissKH Subtitle Downloader

This project is a powerful tool for downloading and decrypting subtitles from [kisskh.ovh](https://kisskh.ovh) using a CLI and GUI interface. 
It supports multi-language subtitle selection, threaded downloads, decryption of protected subtitle formats, and automatic directory handling. 
Built for ease of use and efficiency.

---

## 🧰 Features

- ✅ Download subtitles for selected drama episodes
- ✅ Multi-language support (e.g., `en`, `hi`)
- ✅ Decrypts `.txt`, `.txt1`, `.txt2` encrypted subtitle formats
- ✅ Clean, user-friendly GUI using `tkinter`
- ✅ CSV caching system for metadata reuse
- ✅ CLI and GUI mode available
- ✅ No CMD popup in GUI `.exe` build

---

## 📦 Dependencies

Before running the CLI or GUI, install dependencies:

```bash
pip install -r requirements.txt
```

**`requirements.txt`**
```
tqdm
requests
pandas
playwright
pycryptodome
```

> **Note:** Run `playwright install` after installing requirements:
```bash
playwright install
```

---

## 🖥️ Usage: Command Line

Run the downloader via CLI:

```bash
python cli_v8.py <start_id> [options]
```

### 🔧 Example:

```bash
python cli_v8.py 8982 --ep 1,2,3 --threads 6 --langs en,hi --csv keep
```

### 📘 Options:
| Option            | Description                                                              |
|-------------------|--------------------------------------------------------------------------|
| `<start_id>`      | Required. Drama ID from kisskh.ovh                                       |
| `--end-id`        | Optional. Ending ID range if downloading multiple dramas                 |
| `--ep`            | Comma-separated episodes (e.g., `1,2,3`)                                 |
| `--threads`       | Number of threads to use for fetching metadata                           |
| `--langs`         | Comma, dot, or space-separated language codes (e.g., `en hi`, `en.hi`)   |
| `--csv`           | Whether to `keep` or `delete` metadata CSV files after run               |
| `--meta-skip`     | Reuse existing `drama_details.csv` and `drama_subtitles.csv`             |

---

## 🖱️ Usage: GUI Application

Run the GUI with:

```bash
python gui_v7.py
```

### Or use the pre-built Windows executable:
📦 `gui_v7.exe` (no Python required)

### GUI Features:
- Input drama ID, episodes, languages
- Automatically formats languages (e.g., `en.hi` → `en,hi`)
- Buttons to start download, clear logs, and reset inputs
- Log view with real-time progress output
- No terminal popup window

---

## 📂 Output Structure

All downloaded subtitles are saved as:

```
dramas/
├── Drama Title/
│   ├── Episode_1/
│   │   ├── English.srt
│   │   ├── Hindi.srt
│   └── ...
```

---

## 🧪 Known Issues & Notes

- Encrypted subtitles (.txt variants) are automatically decrypted.
- If antivirus blocks the `.exe`, it’s a false positive. Use `--onedir` build or sign the executable.
- Playwright uses a Chromium browser behind the scenes; ensure it's installed via `playwright install`.

---

## 🚀 Build GUI `.exe`

To build your own GUI `.exe` from `gui_v7.py`:

```bash
pyinstaller --noconsole --onefile --add-data "cli_v8.py;." gui_v7.py
```

Use `--onedir` if antivirus falsely flags the single executable.

---

## 🔓 License

This project is for educational purposes only. Use responsibly. 

---

## 🙌 Credits

Created by PanguPlay
  
Inspired by the structure of KissKH subtitle hosting platform.
