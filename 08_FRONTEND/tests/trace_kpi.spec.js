const { test, expect } = require('@playwright/test');
const fs = require('fs');

test('trace KPI flow and capture console + storage', async ({ page }) => {
  const logs = [];
  page.on('console', (msg) => {
    try {
      logs.push({ type: msg.type(), text: msg.text(), location: msg.location() });
    } catch (e) {
      logs.push({ type: 'unknown', text: String(msg), err: String(e) });
    }
  });

  // Adjust URL if your dev server runs on another port
  const url = process.env.FRONTEND_URL || 'http://localhost:5173/app/analytics?dashboard=direction';
  console.log('TRACE: navigating to', url);
  await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

  // Wait a bit for analytics queries and logs to appear
  await page.waitForTimeout(3000);

  // Try to wait until React Query cache helper exists or timeout
  try {
    await page.waitForFunction(() => !!window.__REACT_QUERY_CACHE, { timeout: 10000 });
  } catch (e) {
    // ignore
  }

  // Collect data from the page
  const rqCache = await page.evaluate(() => (window.__REACT_QUERY_CACHE ? window.__REACT_QUERY_CACHE : null));
  const persisted = await page.evaluate(() => {
    try {
      const raw = window.localStorage.getItem('sp2i:appState');
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return { error: String(e) };
    }
  });
  const session = await page.evaluate(() => {
    try {
      const raw = window.sessionStorage.getItem('sp2i:appState');
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return { error: String(e) };
    }
  });

  // Attempt to call the debug helper if present
  const sp2iDump = await page.evaluate(() => {
    try {
      if (window.__sp2i_dump_state) {
        try {
          const raw = window.localStorage.getItem('sp2i:appState');
          return raw ? JSON.parse(raw) : null;
        } catch (e) {
          return { error: String(e) };
        }
      }
      return null;
    } catch (e) {
      return { error: String(e) };
    }
  });

  // Save output
  const out = { timestamp: new Date().toISOString(), url, logs, rqCache, persisted, session, sp2iDump };
  fs.mkdirSync('08_FRONTEND/test-outputs', { recursive: true });
  fs.writeFileSync('08_FRONTEND/test-outputs/trace_kpi.json', JSON.stringify(out, null, 2), 'utf8');

  console.log('TRACE_SAVED', { logsCount: logs.length, rqKeys: rqCache ? Object.keys(rqCache) : null });

  expect(logs.length).toBeGreaterThan(0);
});
