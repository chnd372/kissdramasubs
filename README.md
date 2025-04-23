
# 🎭 Drama Subtitle Automation Toolkit

This project consists of **two Node.js scripts** that work together to automate the process of scraping drama information and subtitles from [kisskh.ovh](https://kisskh.ovh).

---

## 📦 Components

### 1. `fetch-drama-data.js`
Fetches drama metadata and episode details from the KissKH API and saves it to a CSV file.

### 2. `parallel-fetch-subtitles.js`
Reads the drama details CSV, navigates to each episode page using Puppeteer, extracts subtitle keys (`kkey`), and downloads subtitle data.

---

## 🛠️ Prerequisites

Install the required Node packages:

```bash
npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth axios csv-parser
```

---

## 🧪 Workflow

### 🔹 Step 1: Fetch Drama Data

Run the following script to fetch drama info from KissKH:

```bash
node fetch-drama-data.js
```

This generates a CSV file like `drama_details.csv` containing drama ID, title, episode info, etc.

---

### 🔹 Step 2: Fetch Subtitles in Parallel

Use the drama data CSV to fetch subtitles:

```bash
node parallel-fetch-subtitles.js
```

This script:
- Opens episodes using Puppeteer with stealth mode
- Extracts subtitle `kkey` from network requests or page content
- Downloads subtitle JSON via API
- Saves results to `drama_subtitles.csv`

---

## 📂 File Outputs

- `drama_details.csv`: Contains metadata about each drama and its episodes
- `drama_subtitles.csv`: Contains episode-level subtitle data in JSON format

---

## ⚙️ Configuration

### In `fetch-drama-data.js`:
```js
const startId = 1;
const endId = 1000;
const batchSize = 50;
const delayBetweenBatches = 2000;
```

### In `parallel-fetch-subtitles.js`:
```js
const delayBetweenRequests = 1500;
const maxConcurrentBrowsers = 3;
```

Modify these to control batch sizes, request delays, and concurrency.

---

## 🧠 Tips

- Run both scripts in order: **first fetch dramas**, then **fetch subtitles**.
- Be mindful of rate limits—delays are added to avoid overloading the server.
- Output filenames are auto-incremented to prevent overwriting.

---

## 🛡 Disclaimer

This tool is provided for educational purposes. Respect the terms of service of any website you interact with.
