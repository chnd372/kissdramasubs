# Drama Subtitle Scraper Pipeline

This project provides a complete pipeline to fetch and download subtitles for Asian dramas from KissKh. It involves three main scripts, executed in sequence:

1. **`fetch-drama-data.js`** - Extracts drama metadata (show ID, title, episode info).
2. **`parallel-fetch-subtitles.js`** - Gathers subtitle information for each episode in parallel.
3. **`download_subs.py`** - Downloads subtitle files to the local system.

---

## 📦 Prerequisites

### Common:
- Node.js (>= 14.x)
- Python 3.x
- Internet connection

### Node.js Dependencies:
Install using npm:

```bash
npm install axios csv-parser puppeteer puppeteer-extra puppeteer-extra-plugin-stealth
```

### Python Dependencies:
Install using pip:

```bash
pip install requests pandas tqdm
```

---

## 🔧 Step-by-Step Usage

### 1. Fetch Drama Metadata

**Script**: `fetch-drama-data.js`  
**Output**: `drama_details.csv`

This script scrapes drama titles, show IDs, and episode IDs from the source.

**Run**:
```bash
node fetch-drama-data.js [DramaStartID] [DramaEndID]
```
**Example**: if Drama URL is "https://kisskh.ovh/Drama/Eat-Run-Love?id=9507"
```bash
node fetch-drama-data.js 9507 9507
```
> Modify the script if needed to target a specific genre, range, or source.

---

### 2. Fetch Subtitle Data

**Script**: `parallel-fetch-subtitles.js`  
**Input**: `drama_details.csv`  
**Output**: `drama_subtitles.csv`

This script:
- Parses `drama_details.csv`
- Launches headless browsers using Puppeteer
- Retrieves subtitle API keys (`kkey`)
- Fetches subtitle JSON data from KissKh

**Run**:
```bash
node parallel-fetch-subtitles.js
```

> 🔧 Customizations:
- `delayBetweenRequests`: adjust time between requests to reduce rate-limiting
- `maxConcurrentBrowsers`: change parallelization level
- Modify `puppeteerLaunchOptions` for debugging or browser tweaking

---

### 3. Download Subtitles

**Script**: `download_subs.py`  
**Input**: `drama_subtitles.csv`  
**Output**: subtitle `.vtt` files in `subtitles/` folder

This script:
- Reads subtitle URLs and metadata
- Saves each subtitle to a local file (organized by drama)
- Updated for .txt, .txt1, .txt2, .... file types
- Cleanup CSV files after task completed

**Run**:
```bash
python download_subs.py
```

> 🔧 Customizations:
- Change the subtitle folder structure inside the script
- Add conversion from `.vtt` to `.srt` if needed

---

## ⚙️ Configuration

### In `fetch-drama-data.js`:
```js
const batchSize = 50; #Number of requests to process in parallel
const delayBetweenBatches = 2000; # 2 seconds between batches to avoid rate limiting
```

### In `parallel-fetch-subtitles.js`:
```js
const delayBetweenRequests = 1500; # 1.5 seconds between requests
const maxConcurrentBrowsers = 3; #Maximum number of concurrent browser instances
```

Modify these to control batch sizes, request delays, and concurrency.

### In 'download_subs.py':
```js
time.sleep(1)  # wait after each subtitle
time.sleep(2)  # wait after each episode
```

---

## 🛠️ Output Summary

- `drama_details.csv`: Contains show ID, title, and episode details.
- `drama_subtitles.csv`: Contains subtitle JSON fetched from the API.
- `subtitles/`: Local directory with all downloaded `.vtt` files.

---

## ✅ Troubleshooting

- **Puppeteer crashes**: Ensure Chrome dependencies are installed (`apt install -y libx11-xcb1 libxcb1 libxcomposite1 libxdamage1 libxi6 libxtst6` on Debian).
- **No subtitles fetched**: The page may have changed. Check `kkey` logic in the JS file.
- **Subtitle file missing or broken**: Check network logs or try running slower (`delayBetweenRequests`).

---

## 📂 File Overview

| File | Description |
|------|-------------|
| `fetch-drama-data.js` | Scrapes drama info |
| `parallel-fetch-subtitles.js` | Extracts subtitle metadata via Puppeteer |
| `download_subs.py` | Downloads and saves subtitle files |
| `drama_details.csv` | Intermediate metadata |
| `drama_subtitles.csv` | Metadata with subtitle API results |

---

## 📜 License

This project is for educational purposes only. Use responsibly.

---