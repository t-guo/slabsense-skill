#!/usr/bin/env node
/* Fetch listing details from a real Chrome tab via the DevTools Protocol.

   Start Chrome first:
   node slabsense/scripts/ensure_chrome.js
*/

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { Buffer } = require("node:buffer");

const DEFAULT_DEBUGGER = "http://127.0.0.1:9222";

function usage() {
  console.error(
    "Usage: node slabsense/scripts/browser_listing.js <url> [--output listing.json] [--screenshot page.png] [--debugger http://127.0.0.1:9222]"
  );
}

function parseArgs(argv) {
  const args = { debuggerUrl: DEFAULT_DEBUGGER };
  const positional = [];
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--output" || arg === "-o") {
      args.output = argv[++index];
    } else if (arg === "--screenshot") {
      args.screenshot = argv[++index];
    } else if (arg === "--debugger") {
      args.debuggerUrl = argv[++index];
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      positional.push(arg);
    }
  }
  args.url = positional[0];
  return args;
}

function httpJson(url, method = "GET") {
  return new Promise((resolve, reject) => {
    const request = http.request(url, { method }, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => {
        const body = Buffer.concat(chunks).toString("utf8");
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(`HTTP ${response.statusCode}: ${body.slice(0, 200)}`));
          return;
        }
        try {
          resolve(JSON.parse(body));
        } catch (error) {
          reject(new Error(`Could not parse JSON from ${url}: ${error.message}`));
        }
      });
    });
    request.on("error", reject);
    request.end();
  });
}

function cdpClient(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  let nextId = 1;
  const pending = new Map();
  const listeners = new Map();

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) {
        reject(new Error(message.error.message));
      } else {
        resolve(message.result || {});
      }
    }
    if (message.method && listeners.has(message.method)) {
      for (const listener of listeners.get(message.method)) {
        listener(message.params || {});
      }
    }
  });

  return {
    ready: new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", reject, { once: true });
    }),
    send(method, params = {}) {
      const id = nextId++;
      socket.send(JSON.stringify({ id, method, params }));
      return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
    },
    once(method, timeoutMs = 15000) {
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`Timed out waiting for ${method}`)), timeoutMs);
        const listener = (params) => {
          clearTimeout(timer);
          const current = listeners.get(method) || [];
          listeners.set(
            method,
            current.filter((item) => item !== listener)
          );
          resolve(params);
        };
        listeners.set(method, [...(listeners.get(method) || []), listener]);
      });
    },
    close() {
      socket.close();
    },
  };
}

function extractionExpression() {
  return `(() => {
    const text = (value) => String(value || "").replace(/\\s+/g, " ").trim();
    const meta = (key) => {
      const node = document.querySelector(\`meta[property="\${key}"], meta[name="\${key}"]\`);
      return node ? text(node.getAttribute("content")) : "";
    };
    const visibleText = (selector) => {
      const node = document.querySelector(selector);
      return node ? text(node.innerText || node.textContent) : "";
    };
    const title = text(meta("og:title") || document.title);
    const pageText = text(document.body ? document.body.innerText : "");
    const priceCandidates = [
      meta("product:price:amount"),
      meta("og:price:amount"),
      visibleText("[data-testid='x-price-primary']"),
      visibleText(".x-price-primary"),
      visibleText("[itemprop='price']")
    ].filter(Boolean);
    const imageUrls = Array.from(document.images)
      .map((img) => img.currentSrc || img.src)
      .filter((src) => src && /ebayimg|i\\.ebayimg|thumbs/i.test(src));
    const uniqueImages = Array.from(new Set(imageUrls)).slice(0, 24);
    const gradeMatch = title.match(/\\b(PSA|CGC|BGS|SGC)\\s*(?:GEM\\s*MT|MINT|NM-MT|MT)?\\s*(\\d+(?:\\.\\d)?)\\b/i);
    const priceText = priceCandidates.find((candidate) => /\\d/.test(candidate)) || "";
    const priceMatch = priceText.match(/\\d+(?:,\\d{3})*(?:\\.\\d+)?/);
    const sellerMatch = pageText.match(/\\b([A-Za-z0-9_.-]{2,})\\s*\\((\\d[\\d,]*)\\)\\s*(\\d+(?:\\.\\d+)?)%\\s*positive\\b/i);
    const certMatch = pageText.match(/\\b(?:cert(?:ification)?|PSA\\s*cert)\\D*(\\d{7,10})\\b/i);
    const locationMatch = pageText.match(/(?:Item location|Located in)[:\\s]+([^\\n.]{3,80})/i);
    const returnMatch = pageText.match(/(Seller does not accept returns|No returns|Returns accepted|30 day returns|60 day returns)/i);
    const blocked = /Something went wrong on our end|robot check|captcha|Access Denied/i.test(pageText + " " + title);
    const cleanTitle = title
      .replace(/\\s*\\|\\s*eBay\\s*$/i, "")
      .replace(/\\bPSA\\s*(?:GEM\\s*MT|MINT|NM-MT|MT)?\\s*\\d+(?:\\.\\d)?\\b/ig, "")
      .replace(/\\b(CGC|BGS|SGC)\\s*\\d+(?:\\.\\d)?\\b/ig, "")
      .replace(/\\s+/g, " ")
      .trim();
    return {
      title,
      cleanTitle,
      price: priceMatch ? Number(priceMatch[0].replace(/,/g, "")) : null,
      gradingCompany: gradeMatch ? gradeMatch[1].toUpperCase() : "",
      grade: gradeMatch ? Number(gradeMatch[2]) : null,
      certNumber: certMatch ? certMatch[1] : "",
      sellerUsername: sellerMatch ? sellerMatch[1] : "",
      sellerFeedbackCount: sellerMatch ? Number(sellerMatch[2].replace(/,/g, "")) : null,
      sellerPositivePercent: sellerMatch ? Number(sellerMatch[3]) : null,
      authenticityGuarantee: /Authenticity Guarantee/i.test(pageText),
      returnPolicy: returnMatch ? returnMatch[1] : "",
      itemLocation: locationMatch ? locationMatch[1].trim() : "",
      imageUrls: uniqueImages,
      blocked,
      visibleTextSample: pageText.slice(0, 500)
    };
  })()`;
}

function toListing(url, extracted) {
  const warnings = [];
  if (!extracted.title) warnings.push("listing title was not found");
  if (extracted.price === null) warnings.push("asking price was not found");
  if (extracted.grade === null) warnings.push("grade was not found in the listing title");
  if (extracted.imageUrls.length === 0) warnings.push("listing images were not found");

  if (extracted.blocked) {
    return {
      listing_url: url,
      extraction_status: "blocked",
      listing_notes: "Chrome loaded a marketplace error, captcha, or bot-protection page.",
      photo_quality: "unknown",
      buyer_intent: "unknown",
      extraction_warnings: warnings,
    };
  }

  const canonical = canonicalize(extracted.title || extracted.cleanTitle || "", extracted.gradingCompany || "", extracted.grade);
  return {
    card_name: canonical.canonical_card_name || extracted.cleanTitle || "",
    card_title: canonical.card_title || "",
    card_number: canonical.card_number || "",
    card_number_full: canonical.card_number_full || "",
    set: canonical.set || "",
    year: canonical.year || null,
    language: canonical.language || "",
    grading_company: canonical.grading_company || extracted.gradingCompany || "",
    grade: canonical.grade ?? extracted.grade,
    cert_number: extracted.certNumber || "",
    asking_price: extracted.price,
    listing_url: url,
    listing_notes: `Browser title: ${extracted.title || "not exposed"}. ${
      extracted.imageUrls.length ? "Image URLs were captured; inspect front/back photos manually." : ""
    }`.trim(),
    buyer_intent: "unknown",
    front_image_notes: "",
    back_image_notes: "",
    photo_quality: "unknown",
    seller_username: extracted.sellerUsername || "",
    seller_feedback_count: extracted.sellerFeedbackCount,
    seller_positive_percent: extracted.sellerPositivePercent,
    authenticity_guarantee: Boolean(extracted.authenticityGuarantee),
    return_policy: extracted.returnPolicy || "",
    item_location: extracted.itemLocation || "",
    extraction_status: warnings.length ? "partial" : "ok",
    extraction_warnings: warnings,
    image_urls: extracted.imageUrls,
  };
}

function canonicalize(title, gradingCompany, grade) {
  const script = path.join(__dirname, "canonicalize.py");
  const args = [script, title || ""];
  if (gradingCompany) {
    args.push("--grading-company", gradingCompany);
  }
  if (grade !== null && grade !== undefined) {
    args.push("--grade", String(grade));
  }
  const result = spawnSync("python3", args, { encoding: "utf8" });
  if (result.status !== 0) {
    return {};
  }
  try {
    return JSON.parse(result.stdout);
  } catch {
    return {};
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.url) {
    usage();
    process.exit(args.help ? 0 : 1);
  }

  let target;
  try {
    target = await httpJson(`${args.debuggerUrl}/json/new?${encodeURIComponent(args.url)}`, "PUT");
  } catch (error) {
    console.error(`Could not connect to Chrome DevTools at ${args.debuggerUrl}.`);
    console.error("Start Chrome with: node slabsense/scripts/ensure_chrome.js");
    console.error(error.message);
    process.exit(2);
  }

  const client = cdpClient(target.webSocketDebuggerUrl);
  await client.ready;
  await client.send("Page.enable");
  await client.send("Runtime.enable");
  await client.send("Page.navigate", { url: args.url });
  try {
    await client.once("Page.loadEventFired", 20000);
  } catch {
    // Some marketplace pages keep loading secondary resources; continue with the current DOM.
  }
  await new Promise((resolve) => setTimeout(resolve, 2500));

  const result = await client.send("Runtime.evaluate", {
    expression: extractionExpression(),
    returnByValue: true,
  });
  const extracted = result.result.value;

  if (args.screenshot) {
    const screenshot = await client.send("Page.captureScreenshot", { format: "png", fromSurface: true });
    fs.writeFileSync(args.screenshot, Buffer.from(screenshot.data, "base64"));
  }
  client.close();

  const listing = toListing(args.url, extracted);
  const payload = JSON.stringify(listing, null, 2);
  if (args.output) {
    fs.writeFileSync(args.output, `${payload}\n`, "utf8");
  } else {
    console.log(payload);
  }

  if (listing.extraction_status === "blocked") {
    process.exit(3);
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
