#!/usr/bin/env node
/**
 * Print HTML (with Mermaid) to PDF via Puppeteer.
 * Usage: node scripts/html_to_pdf.mjs <input.html> <output.pdf>
 */
import puppeteer from "puppeteer";
import { pathToFileURL } from "url";
import { resolve } from "path";

const [htmlPath, pdfPath] = process.argv.slice(2);
if (!htmlPath || !pdfPath) {
  console.error("Usage: node html_to_pdf.mjs <input.html> <output.pdf>");
  process.exit(1);
}

const fileUrl = pathToFileURL(resolve(htmlPath)).href;

const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});
const page = await browser.newPage();
await page.goto(fileUrl, { waitUntil: "networkidle0", timeout: 120000 });
await page.waitForFunction(
  () => document.documentElement.getAttribute("data-mermaid-ready") === "true",
  { timeout: 90000 }
);
await page.evaluate(() => new Promise((r) => setTimeout(r, 1500)));
await page.pdf({
  path: resolve(pdfPath),
  format: "A4",
  printBackground: true,
  margin: { top: "16mm", bottom: "18mm", left: "12mm", right: "12mm" },
  displayHeaderFooter: true,
  headerTemplate: "<div></div>",
  footerTemplate:
    '<div style="width:100%;font-size:8px;color:#64748b;text-align:center;padding:0 12mm;">Jaybel Sales Analytics — Architecture Guide · <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
});
await browser.close();
console.log("PDF saved:", resolve(pdfPath));
