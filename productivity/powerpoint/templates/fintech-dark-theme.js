const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// ═══════════════════════════════════
// DARK/LIGHT SANDWICH PPT TEMPLATE
// Adapt for fintech, AI, SaaS decks.
// Features: icons (react-icons+sharp), shadow factories (never reuse options),
//           helper functions, 4 value cards, 3-column layout, table slide,
//           cover/closing dark slides with content slides in light.
// ═══════════════════════════════════

const OUT = "output.pptx";

// ── Palette (change these to match your topic) ──
const C = {
  darkBg:   "0C1929",
  accent:   "0284C7",
  accentLt: "38BDF8",
  green:    "059669",
  purple:   "7C3AED",
  amber:    "D97706",
  red:      "DC2626",
  white:    "FFFFFF",
  text:     "1E293B",
  muted:    "64748B",
  dim:      "94A3B8",
  border:   "E2E8F0",
};

// ── Icons: pick from react-icons/fa, react-icons/md, react-icons/hi, react-icons/bi ──
const { FaBrain, FaRocket, FaUsers, FaHandshake, FaChartLine, FaFileAlt,
  FaCogs, FaCheckCircle, FaShieldAlt, FaProjectDiagram, FaChartBar,
  FaExclamationTriangle, FaClock } = require("react-icons/fa");

function renderIconSvg(Icon, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(Icon, { color, size: String(size) })
  );
}

async function iconToBase64Png(Icon, color, size = 256) {
  const svg = renderIconSvg(Icon, color, size);
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}

// ── Helpers (define at TOP LEVEL — not inside slide scopes) ──
// NEVER reuse option objects — PptxGenJS mutates them. Use factories.
const mkShdw = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 });
const mkShdwLg = () => ({ type: "outer", blur: 8, offset: 2, color: "000000", opacity: 0.12 });

function addSlideNumber(slide, num, total) {
  slide.addText(`${num} / ${total}`, {
    x: 9.0, y: 5.2, w: 0.8, h: 0.3,
    fontSize: 9, color: C.muted, align: "right", fontFace: "Arial",
  });
}

function pageTitle(slide, text, num, total) {
  slide.addText(text, {
    x: 0.6, y: 0.3, w: 8.5, h: 0.55,
    fontSize: 24, fontWeight: "bold", color: C.text, fontFace: "Arial", margin: 0,
  });
  slide.addShape("rect", {
    x: 0.6, y: 0.88, w: 0.8, h: 0.04, fill: { color: C.accent },
  });
  addSlideNumber(slide, num, total);
}

function cardIcon(slide, iconData, x, y, size, bgColor) {
  slide.addShape("roundRect", {
    x, y, w: size, h: size, fill: { color: bgColor }, rectRadius: 0.08,
  });
  slide.addImage({
    data: iconData, x: x + size * 0.2, y: y + size * 0.2,
    w: size * 0.6, h: size * 0.6,
  });
}

function darkSlide(slide) { slide.background = { color: C.darkBg }; }
function lightSlide(slide) { slide.background = { color: C.white }; }

// ═══════════════════════════════════
async function main() {
  // Pre-render all icons once
  const [icBrain, icRocket, icUsers, icHandshake, icChartLine, icFile,
    icCogs, icCheck, icShield, icProject, icChartBar, icWarn, icClock] =
    await Promise.all([
      iconToBase64Png(FaBrain, "#FFFFFF"), iconToBase64Png(FaRocket, "#FFFFFF"),
      iconToBase64Png(FaUsers, "#FFFFFF"), iconToBase64Png(FaHandshake, "#FFFFFF"),
      iconToBase64Png(FaChartLine, "#FFFFFF"), iconToBase64Png(FaFileAlt, "#FFFFFF"),
      iconToBase64Png(FaCogs, "#FFFFFF"), iconToBase64Png(FaCheckCircle, "#FFFFFF"),
      iconToBase64Png(FaShieldAlt, "#FFFFFF"), iconToBase64Png(FaProjectDiagram, "#FFFFFF"),
      iconToBase64Png(FaChartBar, "#FFFFFF"), iconToBase64Png(FaExclamationTriangle, "#FFFFFF"),
      iconToBase64Png(FaClock, "#FFFFFF"),
    ]);

  let pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Team";
  pres.title = "Deck Title";

  // ══ SLIDE 1: COVER (dark) ══
  {
    const s = pres.addSlide();
    darkSlide(s);
    // Decorative orbs
    s.addShape("oval", { x: -1.5, y: -1.5, w: 4.5, h: 4.5, fill: { color: "1D4ED8", transparency: 80 } });
    s.addShape("oval", { x: 7.5, y: 3, w: 4, h: 4, fill: { color: "0EA5E9", transparency: 80 } });
    // Kicker
    s.addText("KICKER TEXT", {
      x: 1, y: 1.7, w: 8, h: 0.4,
      fontSize: 12, color: C.accentLt, fontFace: "Arial", charSpacing: 8, align: "center", margin: 0,
    });
    // Title
    s.addText("Title", {
      x: 1.5, y: 2.1, w: 7, h: 1.2,
      fontSize: 52, fontWeight: "bold", color: C.accentLt, fontFace: "Arial Black",
      align: "center", margin: 0,
    });
    // Subtitle
    s.addText("Subtitle / tagline goes here", {
      x: 1.5, y: 3.1, w: 7, h: 0.5,
      fontSize: 20, color: "CBD5E1", fontFace: "Arial", align: "center", margin: 0,
    });
    addSlideNumber(s, 1, 6);
  }

  // ══ SLIDE 2: THREE CARDS (light) ══
  {
    const s = pres.addSlide();
    lightSlide(s);
    pageTitle(s, "Section Title", 2, 6);
    const cards = [
      { icon: icWarn, title: "Pain 1", desc: "Description text.", color: C.red },
      { icon: icClock, title: "Pain 2", desc: "Description text.", color: C.amber },
      { icon: icShield, title: "Pain 3", desc: "Description text.", color: C.purple },
    ];
    cards.forEach((c, i) => {
      const x = 0.6 + i * 3.1;
      s.addShape("rect", { x, y: 1.3, w: 2.8, h: 3.2, fill: { color: C.white }, shadow: mkShdw() });
      s.addShape("rect", { x, y: 1.3, w: 2.8, h: 0.06, fill: { color: c.color } });
      cardIcon(s, c.icon, x + 1.0, 1.6, 0.6, c.color);
      s.addText(c.title, { x: x + 0.2, y: 2.4, w: 2.4, h: 0.3, fontSize: 16, fontWeight: "bold", color: C.text, fontFace: "Arial", align: "center", margin: 0 });
      s.addText(c.desc, { x: x + 0.2, y: 2.8, w: 2.4, h: 1.0, fontSize: 11, color: C.muted, fontFace: "Arial", align: "center", margin: 0 });
    });
  }

  // ══ SLIDE 3: 2×2 VALUE GRID ══
  {
    const s = pres.addSlide();
    lightSlide(s);
    pageTitle(s, "Value Proposition", 3, 6);
    const vals = [
      { icon: icRocket, color: C.accent, bg: "EFF6FF", title: "Value 1", desc: "Desc." },
      { icon: icUsers, color: C.green, bg: "ECFDF5", title: "Value 2", desc: "Desc." },
      { icon: icHandshake, color: C.purple, bg: "F5F3FF", title: "Value 3", desc: "Desc." },
      { icon: icChartLine, color: C.amber, bg: "FEFCE8", title: "Value 4", desc: "Desc." },
    ];
    vals.forEach((v, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const vx = 0.5 + col * 4.8, vy = 1.3 + row * 1.85;
      s.addShape("rect", { x: vx, y: vy, w: 4.3, h: 1.6, fill: { color: v.bg }, shadow: mkShdwLg() });
      s.addShape("rect", { x: vx, y: vy, w: 0.08, h: 1.6, fill: { color: v.color } });
      cardIcon(s, v.icon, vx + 0.3, vy + 0.35, 0.55, v.color);
      s.addText(v.title, { x: vx + 1.05, y: vy + 0.2, w: 3.0, h: 0.35, fontSize: 17, fontWeight: "bold", color: C.text, fontFace: "Arial", margin: 0 });
      s.addText(v.desc, { x: vx + 1.05, y: vy + 0.55, w: 3.0, h: 0.8, fontSize: 11, color: C.muted, fontFace: "Arial", margin: 0 });
    });
  }

  // ══ SLIDE 4: THREE-COLUMN CARDS ══
  {
    const s = pres.addSlide();
    lightSlide(s);
    pageTitle(s, "Three Columns", 4, 6);
    const cols = [
      { icon: icProject, color: C.purple, bg: "F5F3FF", title: "Col 1", items: ["Point A", "Point B"], output: "→ Output" },
      { icon: icChartBar, color: C.accent, bg: "F0F9FF", title: "Col 2", items: ["Point C", "Point D"], output: "→ Output" },
      { icon: icChartLine, color: C.green, bg: "ECFDF5", title: "Col 3", items: ["Point E", "Point F"], output: "→ Output" },
    ];
    cols.forEach((c, i) => {
      const cx = 0.4 + i * 3.15, cy = 1.3;
      s.addShape("rect", { x: cx, y: cy, w: 2.95, h: 3.2, fill: { color: c.bg }, shadow: mkShdwLg() });
      s.addShape("rect", { x: cx, y: cy, w: 2.95, h: 0.06, fill: { color: c.color } });
      cardIcon(s, c.icon, cx + 1.05, cy + 0.25, 0.55, c.color);
      s.addText(c.title, { x: cx + 0.2, y: cy + 0.95, w: 2.55, h: 0.35, fontSize: 13, fontWeight: "bold", color: C.text, fontFace: "Arial", align: "center", margin: 0 });
      c.items.forEach((item, j) => {
        s.addText(item, { x: cx + 0.3, y: cy + 1.5 + j * 0.35, w: 2.4, h: 0.3, fontSize: 10, color: C.text, fontFace: "Arial", margin: 0, bullet: true });
      });
      s.addShape("roundRect", { x: cx + 0.55, y: cy + 2.55, w: 1.85, h: 0.35, fill: { color: c.color }, rectRadius: 0.17 });
      s.addText(c.output, { x: cx + 0.55, y: cy + 2.55, w: 1.85, h: 0.35, fontSize: 11, fontWeight: "bold", color: C.white, fontFace: "Arial", align: "center", valign: "middle", margin: 0 });
    });
  }

  // ══ SLIDE 5: TABLE ══
  {
    const s = pres.addSlide();
    lightSlide(s);
    pageTitle(s, "Table Slide", 5, 6);
    const rows = [
      [{ text: "Header 1", options: { bold: true, color: C.white, fill: { color: C.darkBg }, fontSize: 10 } },
       { text: "Header 2", options: { bold: true, color: C.white, fill: { color: C.darkBg }, fontSize: 10 } },
       { text: "Header 3", options: { bold: true, color: C.white, fill: { color: C.darkBg }, fontSize: 10 } }],
      [{ text: "Row 1, Col 1", options: { fontSize: 9 } }, { text: "Row 1, Col 2", options: { fontSize: 9 } }, { text: "Row 1, Col 3", options: { fontSize: 9 } }],
      [{ text: "Row 2, Col 1", options: { fontSize: 9 } }, { text: "Row 2, Col 2", options: { fontSize: 9 } }, { text: "Row 2, Col 3", options: { fontSize: 9 } }],
    ];
    s.addTable(rows, {
      x: 0.3, y: 1.3, w: 9.4, colW: [3.0, 2.0, 4.4],
      border: { pt: 0.5, color: C.border },
      fontFace: "Arial",
    });
  }

  // ══ SLIDE 6: CLOSING (dark) ══
  {
    const s = pres.addSlide();
    darkSlide(s);
    s.addShape("oval", { x: -1, y: -1, w: 3.5, h: 3.5, fill: { color: "1D4ED8", transparency: 80 } });
    s.addShape("oval", { x: 7.5, y: 2.5, w: 3.5, h: 3.5, fill: { color: "0EA5E9", transparency: 85 } });
    s.addText("Title", { x: 1.5, y: 1.5, w: 7, h: 1, fontSize: 44, fontWeight: "bold", color: C.accentLt, fontFace: "Arial Black", align: "center", margin: 0 });
    s.addText("Thank you", { x: 1.5, y: 2.5, w: 7, h: 0.5, fontSize: 18, color: "CBD5E1", fontFace: "Arial", align: "center", margin: 0 });
    // Key numbers
    ["A", "B", "C", "D"].forEach((n, i) => {
      s.addText(n, { x: 1.5 + i * 2.0, y: 3.3, w: 1.5, h: 0.5, fontSize: 30, fontWeight: "bold", color: C.white, fontFace: "Arial Black", align: "center", margin: 0 });
    });
    addSlideNumber(s, 6, 6);
  }

  await pres.writeFile({ fileName: OUT });
  console.log("Done:", OUT);
}

main().catch(e => { console.error(e); process.exit(1); });
