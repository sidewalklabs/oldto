#!/usr/bin/env node
// install puppeteer globally and use a recent enough node for the async and await syntax
const path = process.argv[2]

const puppeteer = require('puppeteer');

function pause() {
  return new Promise( (resolve, reject) => {
    setTimeout(resolve, 3000);
  })
}

(async () => {
  let browser = null
  try {
    browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.setViewport({width:2880, height:1800});
    await page.goto('http://localhost:8000');
    console.log('allow to load')
    await pause();
    await page.screenshot({path: path});
    process.exit();
  } catch(err) {
    console.error(err);
    if (browser) {
      await browser.close();
    }
 }
})()
