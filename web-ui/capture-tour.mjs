import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 2 // retina for crisp screenshots
  });
  const page = await context.newPage();

  const htmlPath = path.join(__dirname, 'tour-mockup.html');
  const fileUrl = 'file://' + htmlPath;

  await page.goto(fileUrl);
  // Wait for the auto-start tour
  await page.waitForTimeout(800);

  for (let step = 0; step < 8; step++) {
    // Navigate to step
    await page.evaluate((s) => window.tourGo(s), step);
    // Wait for positioning/layout to settle
    await page.waitForTimeout(400);

    const screenshotPath = path.join(__dirname, `tour-step-${step + 1}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`✓ Saved ${screenshotPath}`);
  }

  await browser.close();
  console.log('\nAll 8 tour screenshots captured!');
})();
