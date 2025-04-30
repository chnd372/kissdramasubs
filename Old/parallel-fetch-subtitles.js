// Save this as fetch-subtitles-enhanced.js
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const axios = require('axios');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

// Add stealth plugin
puppeteer.use(StealthPlugin());

// Configuration
const csvFilePath = 'drama_details.csv';
const outputFile = getUniqueFilename('drama_subtitles.csv');
const delayBetweenRequests = 1500; // 1.5 seconds between requests
const maxConcurrentBrowsers = 3; // Maximum number of concurrent browser instances
const puppeteerLaunchOptions = {
    headless: true,
    args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
        '--window-size=1920x1080',
    ],
    timeout: 60000 // Increase timeout to 60 seconds
};

// Find a unique filename with incrementing numbers
function getUniqueFilename(baseFilename) {
    let filename = baseFilename;
    let counter = 1;
    
    const ext = path.extname(baseFilename);
    const name = path.basename(baseFilename, ext);
    
    while (fs.existsSync(filename)) {
        filename = `${name}${counter}${ext}`;
        counter++;
    }
    
    return filename;
}

// CSV Header for output
const csvHeader = 'Show ID,Episode ID,Episode Number,Drama Title,Drama Link,Subtitle Link,Subtitle Data\n';
fs.writeFileSync(outputFile, csvHeader);

// Function to sanitize content for CSV
function sanitizeForCSV(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/"/g, '""');
}

// Function to parse episode details from the CSV
function parseEpisodeDetails(details) {
    const episodes = [];
    const regex = /Episode (\d+) \(ID: (\d+), Subtitles: (\d+)\)/g;
    let match;
    
    while ((match = regex.exec(details)) !== null) {
        episodes.push({
            number: match[1],
            id: match[2],
            subtitles: match[3]
        });
    }
    
    return episodes;
}

// Function to extract the kkey from a webpage
async function extractKkey(page, showId, episodeId, episodeNumber) {
    try {
        // Navigate to the episode page
        const url = `https://kisskh.ovh/Drama/a/Episode-${episodeNumber}?id=${showId}&ep=${episodeId}`;
        console.log(`Navigating to ${url}`);
        
        // First disable any existing request interception
        if (page._client) {
            await page.setRequestInterception(false).catch(() => {});
        }
        
        // Set up the kkey capture
        let kkey = null;
        let responseListener = null;
        
        const kkeyPromise = new Promise(resolve => {
            // Set up a listener for the response
            responseListener = async response => {
                const url = response.url();
                if (url.includes(`/api/Sub/${episodeId}?kkey=`)) {
                    const keyMatch = url.match(/kkey=([^&]+)/);
                    if (keyMatch && keyMatch[1]) {
                        kkey = keyMatch[1];
                        resolve(kkey);
                    }
                }
            };
            
            page.on('response', responseListener);
        });
        
        // Navigate to the page
        await page.goto(url, { 
            waitUntil: 'networkidle2', 
            timeout: 30000 
        });
        
        // Wait for the kkey to be captured or timeout
        await Promise.race([
            kkeyPromise,
            new Promise(resolve => setTimeout(resolve, 15000))
        ]);
        
        // Clean up the listener
        if (responseListener) {
            page.off('response', responseListener);
        }
        
        // If kkey wasn't found in network traffic, try to extract it from page content
        if (!kkey) {
            console.log("Attempting to extract kkey from page content...");
            try {
                const content = await page.content();
                const match = content.match(new RegExp(`/api/Sub/${episodeId}\\?kkey=([^"&]+)`));
                
                if (match && match[1]) {
                    kkey = match[1];
                    console.log(`Found kkey in page content: ${kkey}`);
                }
            } catch (err) {
                console.error("Error extracting kkey from page content:", err.message);
            }
        }
        
        // As a final attempt, try to extract from page evaluation
        if (!kkey) {
            console.log("Attempting to extract kkey using page evaluation...");
            try {
                kkey = await page.evaluate((episodeId) => {
                    try {
                        const scripts = document.querySelectorAll('script');
                        for (const script of scripts) {
                            if (!script.textContent) continue;
                            const text = script.textContent;
                            if (text && text.includes(`/api/Sub/${episodeId}?kkey=`)) {
                                const match = text.match(new RegExp(`/api/Sub/${episodeId}\\?kkey=([^"&]+)`));
                                if (match && match[1]) {
                                    return match[1];
                                }
                            }
                        }
                        
                        // Try to find in XHR calls that might be in the page
                        const allElements = document.querySelectorAll('*');
                        for (const el of allElements) {
                            const dataAttributes = el.getAttributeNames().filter(name => name.startsWith('data-'));
                            for (const attr of dataAttributes) {
                                const value = el.getAttribute(attr);
                                if (value && value.includes(`/api/Sub/${episodeId}?kkey=`)) {
                                    const match = value.match(new RegExp(`/api/Sub/${episodeId}\\?kkey=([^"&]+)`));
                                    if (match && match[1]) {
                                        return match[1];
                                    }
                                }
                            }
                        }
                        
                        return null;
                    } catch (err) {
                        console.error("Error in page.evaluate:", err);
                        return null;
                    }
                }, episodeId).catch(() => null);
                
                if (kkey) {
                    console.log(`Found kkey using page evaluation: ${kkey}`);
                }
            } catch (err) {
                console.error("Error during page evaluation:", err.message);
            }
        }
        
        return kkey;
    } catch (error) {
        console.error(`Error extracting kkey: ${error.message}`);
        return null;
    }
}

// Function to fetch subtitle data using axios
async function fetchSubtitleData(kkey, episodeId) {
    try {
        const subtitleUrl = `https://kisskh.ovh/api/Sub/${episodeId}?kkey=${kkey}`;
        console.log(`Fetching subtitle data from ${subtitleUrl}`);
        
        const response = await axios.get(subtitleUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://kisskh.ovh/',
                'Accept': 'application/json'
            },
            timeout: 10000
        });
        
        return response.data;
    } catch (error) {
        console.error(`Error fetching subtitle data: ${error.message}`);
        return null;
    }
}

// Process an individual episode
async function processEpisode(browser, showId, title, episode) {
    const page = await browser.newPage().catch(err => {
        console.error("Error creating new page:", err);
        return null;
    });
    
    if (!page) return false;
    
    try {
        await page.setViewport({ width: 1920, height: 1080 });
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
        await page.setDefaultNavigationTimeout(30000);
        await page.setDefaultTimeout(30000);
        
        // Generate the drama link
        const dramaLink = `https://kisskh.ovh/Drama/a/Episode-${episode.number}?id=${showId}&ep=${episode.id}`;
        
        // Extract the kkey
        const kkey = await extractKkey(page, showId, episode.id, episode.number);
        
        if (!kkey) {
            console.error(`Could not extract kkey for episode ${episode.number} of "${title}"`);
            return false;
        }
        
        // Generate the subtitle API link
        const subtitleLink = `https://kisskh.ovh/api/Sub/${episode.id}?kkey=${kkey}`;
        
        // Fetch the subtitle data
        const subtitleData = await fetchSubtitleData(kkey, episode.id);
        
        if (!subtitleData) {
            console.error(`Failed to fetch subtitle data for episode ${episode.number} of "${title}"`);
            return false;
        }
        
        // Write the data to the CSV
        const row = [
            `"${sanitizeForCSV(showId)}"`,
            `"${sanitizeForCSV(episode.id)}"`,
            `"${sanitizeForCSV(episode.number)}"`,
            `"${sanitizeForCSV(title)}"`,
            `"${sanitizeForCSV(dramaLink)}"`,
            `"${sanitizeForCSV(subtitleLink)}"`,
            `"${sanitizeForCSV(JSON.stringify(subtitleData))}"`
        ];
        
        fs.appendFileSync(outputFile, row.join(',') + '\n');
        console.log(`Processed episode ${episode.number} for "${title}"`);
        return true;
    } catch (error) {
        console.error(`Error processing episode ${episode.number} for "${title}":`, error);
        return false;
    } finally {
        await page.close().catch(() => {});
    }
}

// Function to process a batch of episodes in parallel
async function processBatch(browser, showId, title, episodes, batchSize) {
    const batches = [];
    for (let i = 0; i < episodes.length; i += batchSize) {
        batches.push(episodes.slice(i, i + batchSize));
    }
    
    let successCount = 0;
    let failCount = 0;
    
    for (const batch of batches) {
        const results = await Promise.all(
            batch.map(episode => processEpisode(browser, showId, title, episode))
        );
        
        successCount += results.filter(result => result).length;
        failCount += results.filter(result => !result).length;
        
        // Small delay between batches to avoid overloading the server
        await new Promise(resolve => setTimeout(resolve, delayBetweenRequests));
    }
    
    return { successCount, failCount };
}

// Main function to process the CSV and fetch subtitle data
async function processCSV() {
    return new Promise((resolve, reject) => {
        const dramas = [];
        
        fs.createReadStream(csvFilePath)
            .pipe(csv())
            .on('data', (row) => {
                dramas.push(row);
            })
            .on('end', () => {
                console.log(`CSV file successfully processed. Found ${dramas.length} dramas.`);
                resolve(dramas);
            })
            .on('error', (error) => {
                reject(error);
            });
    });
}

// Function to process dramas in parallel batches
async function processDramasInParallel(dramas, maxConcurrent) {
    // Launch a browser
    console.log("Launching browser...");
    let browser = null;
    let retries = 3;
    
    while (retries > 0) {
        try {
            browser = await puppeteer.launch(puppeteerLaunchOptions);
            break;
        } catch (error) {
            console.error(`Failed to launch browser: ${error.message}`);
            retries--;
            if (retries === 0) {
                throw new Error("Could not launch browser after multiple attempts");
            }
            console.log(`Retrying in 5 seconds... (${retries} attempts left)`);
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
    }
    
    // Function to process a single drama
    async function processDrama(drama) {
        const showId = drama['Show ID'];
        const title = drama['Title'];
        const episodeDetailsText = drama['Episode Details'];
        
        // Parse episode details
        const episodes = parseEpisodeDetails(episodeDetailsText);
        console.log(`Processing Drama "${title}" (ID: ${showId}) with ${episodes.length} episodes.`);
        
        // Process episodes in parallel batches (3 at a time)
        const { successCount, failCount } = await processBatch(browser, showId, title, episodes, 3);
        
        return { successCount, failCount };
    }
    
    // Process dramas in batches
    const results = { successCount: 0, failCount: 0 };
    
    // Process dramas in sequence but episodes in parallel
    for (const drama of dramas) {
        const result = await processDrama(drama);
        results.successCount += result.successCount;
        results.failCount += result.failCount;
    }
    
    await browser.close();
    return results;
}

// Main execution function
async function main() {
    try {
        console.log(`Reading drama data from ${csvFilePath}...`);
        const dramas = await processCSV();
        
        const startTime = Date.now();
        
        console.log("Processing dramas and fetching subtitle data...");
        const results = await processDramasInParallel(dramas, maxConcurrentBrowsers);
        
        const totalTime = ((Date.now() - startTime) / 60000).toFixed(2);
        console.log(`\nProcess completed in ${totalTime} minutes.`);
        console.log(`Total episodes processed: ${results.successCount} successful, ${results.failCount} failed`);
        console.log(`Results saved to ${path.resolve(outputFile)}`);
        
    } catch (error) {
        console.error("Error in main process:", error);
    }
}

// Execute the main function
main();
