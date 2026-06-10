#!/usr/bin/env node
/* Ensure an isolated Chrome DevTools session is available for browser_listing.js. */

const http = require("node:http");
const { spawn } = require("node:child_process");

const DEFAULT_DEBUGGER = "http://127.0.0.1:9222";
const DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const DEFAULT_USER_DATA_DIR = "/tmp/slabsense-chrome";

function usage() {
  console.error(
    [
      "Usage: node slabsense/scripts/ensure_chrome.js [options]",
      "",
      "Options:",
      "  --debugger <url>       DevTools URL, default http://127.0.0.1:9222",
      "  --chrome <path>        Chrome executable path",
      "  --user-data-dir <dir>  Isolated Chrome profile directory",
      "  --timeout <ms>         Startup wait, default 10000",
      "  --check-only           Exit 0 if available, 2 if unavailable",
    ].join("\n")
  );
}

function parseArgs(argv) {
  const args = {
    debuggerUrl: DEFAULT_DEBUGGER,
    chromePath: DEFAULT_CHROME,
    userDataDir: DEFAULT_USER_DATA_DIR,
    timeoutMs: 10000,
    checkOnly: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--debugger") {
      args.debuggerUrl = argv[++index];
    } else if (arg === "--chrome") {
      args.chromePath = argv[++index];
    } else if (arg === "--user-data-dir") {
      args.userDataDir = argv[++index];
    } else if (arg === "--timeout") {
      args.timeoutMs = Number(argv[++index]);
    } else if (arg === "--check-only") {
      args.checkOnly = true;
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function httpJson(url) {
  return new Promise((resolve, reject) => {
    const request = http.request(url, { method: "GET", timeout: 1500 }, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => {
        const body = Buffer.concat(chunks).toString("utf8");
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(`HTTP ${response.statusCode}: ${body.slice(0, 160)}`));
          return;
        }
        try {
          resolve(JSON.parse(body));
        } catch (error) {
          reject(new Error(`Could not parse JSON from ${url}: ${error.message}`));
        }
      });
    });
    request.on("timeout", () => {
      request.destroy(new Error(`Timed out connecting to ${url}`));
    });
    request.on("error", reject);
    request.end();
  });
}

async function isChromeReady(debuggerUrl) {
  try {
    const version = await httpJson(`${debuggerUrl}/json/version`);
    return Boolean(version.Browser || version.webSocketDebuggerUrl);
  } catch {
    return false;
  }
}

async function waitUntilReady(debuggerUrl, timeoutMs) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (await isChromeReady(debuggerUrl)) {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  return false;
}

function debuggerPort(debuggerUrl) {
  return new URL(debuggerUrl).port || "9222";
}

function startChrome(args) {
  const chromeArgs = [
    `--remote-debugging-port=${debuggerPort(args.debuggerUrl)}`,
    `--user-data-dir=${args.userDataDir}`,
    "about:blank",
  ];
  const child = spawn(args.chromePath, chromeArgs, {
    detached: true,
    stdio: "ignore",
  });
  child.unref();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    return;
  }

  if (await isChromeReady(args.debuggerUrl)) {
    console.log(`Chrome DevTools is ready at ${args.debuggerUrl}`);
    return;
  }

  if (args.checkOnly) {
    console.error(`Chrome DevTools is not available at ${args.debuggerUrl}`);
    process.exit(2);
  }

  startChrome(args);
  if (!(await waitUntilReady(args.debuggerUrl, args.timeoutMs))) {
    console.error(`Started Chrome, but DevTools was not ready at ${args.debuggerUrl} within ${args.timeoutMs}ms.`);
    process.exit(2);
  }
  console.log(`Chrome DevTools is ready at ${args.debuggerUrl}`);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
