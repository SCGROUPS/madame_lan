const fs = require('fs');
const { exec } = require('child_process');
const yaml = require('js-yaml');
const { v4: uuidv4 } = require('uuid');
const path = require('path');
const arrivalRates = [10, 20, 50, 100, 200, 500];
const reportDirectory = path.resolve(__dirname, '../report');
const ymlTemplatePath = path.resolve(__dirname, 'dev-load-test-template.yml');
const ymlPath = path.resolve(__dirname, 'dev-load-test.yml');
let logFile = path.join(reportDirectory, 'summary.log');

if (!fs.existsSync(reportDirectory)) {
    fs.mkdirSync(reportDirectory);
}

function modifyYml(arrivalRate) {
    const template = fs.readFileSync(ymlTemplatePath, 'utf8');
    const config = yaml.load(template);

    config.config.phases[0].arrivalRate = arrivalRate;

    fs.writeFileSync(ymlPath, yaml.dump(config), 'utf8');
}

function runTest(arrivalRate) {
    return new Promise((resolve, reject) => {
        console.log(`Running test with arrival rate: ${arrivalRate}`);
        const startTime = Date.now();
        exec('npm run test', (error, stdout, stderr) => {
            if (error) {
                console.error(`Error running test with arrival rate ${arrivalRate}: ${error}`);
                return reject(error);
            }
            const endTime = Date.now();
            const duration = (endTime - startTime) / 1000;
            const report = {
                arrivalRate,
                duration,
                stdout,
                stderr
            };
            fs.writeFileSync(path.join(reportDirectory, `report_${arrivalRate}.json`), JSON.stringify(report, null, 2), 'utf8');

            const summaryStart = stdout.indexOf('--------------------------------\nSummary report @');
            const summaryEnd = stdout.indexOf('Log file:', summaryStart);
            const summary = stdout.substring(summaryStart, summaryEnd).trim();

            resolve(summary);
        });
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

(async function () {
    let postfix = '';
    let counter = 1;
    while (fs.existsSync(logFile)) {
        postfix = `_${counter}`;
        logFile = path.join(reportDirectory, `summary${postfix}.log`);
        counter++;
    }

    for (const rate of arrivalRates) {
        modifyYml(rate);
        try {
            const summary = await runTest(rate);
            const summaryHeader = `Summary report for arrival rate ${rate} @ ${new Date().toLocaleTimeString()}\n`;
            fs.writeFileSync(logFile, `${summaryHeader}${summary}\n\n`, { flag: 'a' }); // Use 'a' flag to append to the file
        } catch (error) {
            console.error(`Failed to run test for arrival rate ${rate}`);
        }
        console.log(`Test for arrival rate ${rate} completed. Waiting 30 secs before next test...`);
        await sleep(30000);
    }
    console.log('All tests completed. Reports are saved in the reports directory.');
})();