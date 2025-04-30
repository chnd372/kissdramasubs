// Save this as fetch-drama-data.js
const fs = require('fs');
const https = require('https');
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node fetch-drama-data.js [startId] [endId]');
  console.error('Example: node fetch-drama-data.js 500 501');
  process.exit(1);
}

// Configuration
const startId = parseInt(args[0], 10);
const endId = parseInt(args[1], 10);

// Validate inputs
if (isNaN(startId) || isNaN(endId)) {
  console.error('Error: startId and endId must be numbers');
  process.exit(1);
}

if (startId > endId) {
  console.error('Error: startId must be less than or equal to endId');
  process.exit(1);
}

const batchSize = 50; // Number of requests to process in parallel
const baseOutputFile = 'drama_details.csv';
const baseUrl = 'https://kisskh.ovh/api/DramaList/Drama/';
const delayBetweenBatches = 2000; // 2 seconds between batches to avoid rate limiting

// Find a unique filename with incrementing numbers
function getUniqueFilename(baseFilename) {
    let filename = baseFilename;
    let counter = 1;
    
    // Extract base name and extension
    const ext = path.extname(baseFilename);
    const name = path.basename(baseFilename, ext);
    
    // Check if file exists, increment counter until finding a unique name
    while (fs.existsSync(filename)) {
        filename = `${name}${counter}${ext}`;
        counter++;
    }
    
    return filename;
}

// Get unique filename for our output
const outputFile = getUniqueFilename(baseOutputFile);
console.log(`Using output file: ${outputFile}`);

// CSV Header
const csvHeader = 'Show ID,Title,Total Episodes,Thumbnail URL,Description,Release Date,Country,Status,Type,Episode Details\n';
fs.writeFileSync(outputFile, csvHeader);

// Function to sanitize content for CSV
function sanitizeForCSV(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/"/g, '""');
}

// Function to process drama data
function processDramaData(data) {
    try {
        // Check if the data has the expected structure
        if (!data || !data.id || !data.title) {
            return null;
        }

        // Format episode details as a readable string
        const episodeDetails = data.episodes ? 
            data.episodes.map(ep => 
                `Episode ${ep.number} (ID: ${ep.id}, Subtitles: ${ep.sub})`
            ).join('; ') : '';
        
        // Create CSV row
        const row = [
            `"${sanitizeForCSV(data.id)}"`,
            `"${sanitizeForCSV(data.title)}"`,
            `"${sanitizeForCSV(data.episodesCount)}"`,
            `"${sanitizeForCSV(data.thumbnail)}"`,
            `"${sanitizeForCSV(data.description)}"`,
            `"${sanitizeForCSV(data.releaseDate)}"`,
            `"${sanitizeForCSV(data.country)}"`,
            `"${sanitizeForCSV(data.status)}"`,
            `"${sanitizeForCSV(data.type)}"`,
            `"${sanitizeForCSV(episodeDetails)}"`
        ];
        
        return row.join(',') + '\n';
    } catch (error) {
        console.error(`Error processing data for ID ${data?.id}:`, error);
        return null;
    }
}

// Function to fetch data from a URL with a promise
function fetchData(id) {
    return new Promise((resolve, reject) => {
        const url = `${baseUrl}${id}`;
        console.log(`Fetching ${url}`);
        
        https.get(url, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                if (res.statusCode !== 200) {
                    console.log(`Request failed for ID ${id} with status code ${res.statusCode}`);
                    resolve(null); // Don't reject, just return null
                    return;
                }
                
                try {
                    const jsonData = JSON.parse(data);
                    resolve(jsonData);
                } catch (e) {
                    console.error(`Error parsing JSON for ID ${id}:`, e.message);
                    resolve(null);
                }
            });
        }).on('error', (err) => {
            console.error(`Request error for ID ${id}:`, err.message);
            resolve(null); // Don't reject, just return null
        });
    });
}

// Main function to process in batches
async function processBatches() {
    const startTime = Date.now();
    let successCount = 0;
    let failCount = 0;
    
    console.log(`Starting to fetch drama data from ID ${startId} to ${endId}...`);
    
    for (let batchStart = startId; batchStart <= endId; batchStart += batchSize) {
        const batchEnd = Math.min(batchStart + batchSize - 1, endId);
        console.log(`\nProcessing batch: ${batchStart} to ${batchEnd}`);
        
        // Create an array of promises for this batch
        const promises = [];
        for (let id = batchStart; id <= batchEnd; id++) {
            promises.push(fetchData(id));
        }
        
        // Wait for all promises in this batch to resolve
        const results = await Promise.all(promises);
        
        // Process results and append to CSV
        let batchData = '';
        for (const data of results) {
            if (data) {
                const csvLine = processDramaData(data);
                if (csvLine) {
                    batchData += csvLine;
                    successCount++;
                } else {
                    failCount++;
                }
            } else {
                failCount++;
            }
        }
        
        // Append batch data to file
        if (batchData) {
            fs.appendFileSync(outputFile, batchData);
        }
        
        // Calculate and display progress
        const totalProcessed = successCount + failCount;
        const percentComplete = ((totalProcessed / (endId - startId + 1)) * 100).toFixed(2);
        const elapsedMs = Date.now() - startTime;
        const msPerItem = elapsedMs / totalProcessed;
        const remainingItems = endId - startId + 1 - totalProcessed;
        const estimatedRemainingMs = msPerItem * remainingItems;
        const remainingMinutes = Math.ceil(estimatedRemainingMs / 60000);
        
        console.log(`Progress: ${percentComplete}% (${totalProcessed}/${endId - startId + 1})`);
        console.log(`Success: ${successCount}, Failed: ${failCount}`);
        console.log(`Estimated time remaining: ${remainingMinutes} minutes`);
        
        // Add delay between batches to avoid overwhelming the server
        if (batchEnd < endId) {
            console.log(`Waiting ${delayBetweenBatches/1000}s before next batch...`);
            await new Promise(resolve => setTimeout(resolve, delayBetweenBatches));
        }
    }
    
    const totalTime = ((Date.now() - startTime) / 60000).toFixed(2);
    console.log(`\nProcess completed in ${totalTime} minutes.`);
    console.log(`Total dramas processed: ${successCount} successful, ${failCount} failed`);
    console.log(`Results saved to ${path.resolve(outputFile)}`);
}

// Start the process
processBatches().catch(err => {
    console.error('An error occurred in the main process:', err);
});