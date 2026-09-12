// Post-build smoke (READ-ONLY, sans dependance ajoutee) :
// sert dist/ en local et verifie qu'aucune erreur runtime ne bloque le montage React.
//   - pageerror count == 0
//   - #root non vide (childElementCount > 0)
// Usage : npm run build && npm run test:postbuild
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const playwright = require("playwright");

const DIST = path.resolve(__dirname, "..", "dist");

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".map": "application/json",
};

function createStaticServer() {
  return http.createServer((request, response) => {
    const urlPath = decodeURIComponent(String(request.url || "/").split("?")[0]);
    let filePath = path.join(DIST, urlPath);
    if (!filePath.startsWith(DIST)) {
      response.writeHead(403);
      response.end();
      return;
    }
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      filePath = path.join(DIST, "index.html"); // repli SPA
    }
    response.writeHead(200, { "Content-Type": MIME[path.extname(filePath).toLowerCase()] || "application/octet-stream" });
    fs.createReadStream(filePath).pipe(response);
  });
}

(async () => {
  if (!fs.existsSync(path.join(DIST, "index.html"))) {
    console.log("POSTBUILD_SMOKE: FAIL (dist/index.html absent -> executer npm run build)");
    process.exit(1);
  }

  const server = createStaticServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();

  const browser = await playwright.chromium.launch();
  const page = await browser.newPage();
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(String(error.message).slice(0, 200)));

  let rootChildren = -1;
  try {
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "load", timeout: 60000 });
    await page.waitForTimeout(6000);
    rootChildren = await page.evaluate(() => {
      const root = document.getElementById("root");
      return root ? root.childElementCount : -1;
    });
  } catch (error) {
    console.log("POSTBUILD_SMOKE: FAIL (navigation) " + String(error.message).split("\n")[0]);
  } finally {
    await browser.close();
    server.close();
  }

  console.log("PAGE_ERRORS:", pageErrors.length);
  pageErrors.slice(0, 5).forEach((message) => console.log("  ERR:", message));
  console.log("ROOT_CHILD_COUNT:", rootChildren);

  if (pageErrors.length === 0 && rootChildren > 0) {
    console.log("POSTBUILD_SMOKE: PASS");
    process.exit(0);
  }
  console.log("POSTBUILD_SMOKE: FAIL");
  process.exit(1);
})();
