// Usage: node render.js stills 0.4,1.8,...   |   node render.js video
const puppeteer = require('puppeteer-core');
const ffmpeg = require('ffmpeg-static');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const FPS = 30;
const url = 'file:///' + path.join(__dirname, 'composition.html').replace(/\\/g, '/');

(async () => {
  const mode = process.argv[2] || 'stills';
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--hide-scrollbars', '--force-color-profile=srgb'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: 'networkidle0' });
  await page.evaluate(() => window.ready);
  const duration = await page.evaluate(() => window.DURATION);

  if (mode === 'stills') {
    const times = (process.argv[3] || '').split(',').map(Number);
    fs.mkdirSync(path.join(__dirname, 'stills'), { recursive: true });
    for (const t of times) {
      await page.evaluate((t) => window.render(t), t);
      await page.screenshot({ path: path.join(__dirname, 'stills', `t${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 85 });
    }
  } else {
    const out = path.join(__dirname, 'video_noaudio.mp4');
    const ff = spawn(ffmpeg, ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'medium', out], { stdio: ['pipe', 'ignore', 'inherit'] });
    const total = Math.round(duration * FPS);
    for (let f = 0; f < total; f++) {
      await page.evaluate((t) => window.render(t), f / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 60 === 0) console.log(`frame ${f}/${total}`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('wrote', out);
  }
  await browser.close();
})();
