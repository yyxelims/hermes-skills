#!/usr/bin/env node
/**
 * Fintech PPTX Builder Template — pptxgenjs
 * 
 * Design system features:
 *   - Semantic color palette (dark, blue, purple, green, orange)
 *   - Card factory: white bg + shadow + top 4px accent bar
 *   - Icon pipeline: react-icons (FontAwesome) → sharp → base64 PNG
 *   - Cover/closing dark slides, pain-point cards, flow charts, swimlanes
 *   - Shadow factories (NEVER reuse option objects — pptxgenjs mutates them)
 *   - RECTANGLE not ROUNDED_RECTANGLE for accent-bar cards
 * 
 * Usage: Edit the C palette and slide blocks, then `node build.js`
 * Requirements: npm install pptxgenjs react-icons react react-dom sharp
 */

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// ── Icons (pick what you need from react-icons/fa) ──
const { FaBrain, FaFileAlt, FaLock, FaPen, FaRobot, FaChartBar,
  FaDesktop, FaProjectDiagram, FaChartLine, FaDownload, FaBullseye,
  FaBolt, FaGem, FaLightbulb, FaShieldAlt, FaHandshake, FaStar,
  FaClock, FaUsers, FaFilter, FaCheckCircle, FaTimesCircle,
  FaCogs, FaSearch, FaLink, FaArrowRight, FaExchangeAlt,
  FaUserCheck, FaNetworkWired, FaDatabase } = require("react-icons/fa");

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

// ── Palette (customize for your project) ──
const C = {
  dark:    "1B2A4A",
  blue:    "2B7DE9",
  purple:  "7C4DFF",
  green:   "21A366",
  orange:  "E8710A",
  white:   "FFFFFF",
  text:    "1E293B",
  muted:   "64748B",
  dim:     "94A3B8",
  border:  "E2E8F0",
  lightBg: "F8FAFC",
  blueBg:  "EBF4FF",
  purpleBg:"F3EEFF",
  greenBg: "E6F9F1",
  orangeBg:"FEF3E8",
};

// ── Shadow factories (NEVER reuse — pptxgenjs mutates them) ──
const mkShdw = () => ({ type: "outer", blur: 4, offset: 1, color: "000000", opacity: 0.10 });
const mkShdwMd = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.12 });

// ── Reusable helpers ──
function addSlideNum(slide, num, total = 9) {
  slide.addText(`${num} / ${total}`, {
    x: 9.0, y: 5.15, w: 0.8, h: 0.3,
    fontSize: 9, color: C.muted, fontFace: "Arial", align: "right",
  });
}

function pageTitle(slide, text, num) {
  slide.addText(text, {
    x: 0.6, y: 0.25, w: 8.5, h: 0.5,
    fontSize: 26, bold: true, color: C.text, fontFace: "Arial", margin: 0,
  });
  slide.addShape("rect", {
    x: 0.6, y: 0.78, w: 0.7, h: 0.04, fill: { color: C.blue },
  });
  addSlideNum(slide, num);
}

function iconBox(slide, iconData, x, y, size, bgColor) {
  slide.addShape("roundRect", {
    x, y, w: size, h: size, fill: { color: bgColor }, rectRadius: 0.08,
  });
  const pad = size * 0.22;
  slide.addImage({
    data: iconData, x: x + pad, y: y + pad, w: size - 2 * pad, h: size - 2 * pad,
  });
}

/** Standard card: white bg + shadow + top 4px accent bar + icon circle + title + desc */
function addCard(slide, x, y, w, h, color, iconData, title, desc, opts = {}) {
  slide.addShape("rect", { x, y, w, h, fill: { color: C.white }, shadow: mkShdwMd() });
  slide.addShape("rect", { x, y, w, h: 0.053, fill: { color } });
  iconBox(slide, iconData, x + w / 2 - 0.3, y + 0.25, 0.6, color);
  slide.addText(title, {
    x: x + 0.15, y: y + 1.0, w: w - 0.3, h: 0.35,
    fontSize: opts.titleFontSize || 15, bold: true, color: C.text, align: "center", margin: 0,
  });
  slide.addText(desc, {
    x: x + 0.15, y: y + 1.4, w: w - 0.3, h: h - 1.6,
    fontSize: opts.descFontSize || 10.5, color: C.muted, align: "center", margin: 0, valign: "top",
  });
}

/** Small agent card for swimlane diagrams */
function agentCard(slide, x, y, w, h, color, iconData, name, func) {
  slide.addShape("rect", { x, y, w, h, fill: { color: C.white }, shadow: mkShdw() });
  slide.addShape("rect", { x, y, w, h: 0.035, fill: { color } });
  iconBox(slide, iconData, x + 0.1, y + 0.15, 0.32, color);
  slide.addText(name, {
    x: x + 0.5, y: y + 0.1, w: w - 0.6, h: 0.3,
    fontSize: 10.5, bold: true, color: C.text, margin: 0,
  });
  slide.addText(func, {
    x: x + 0.5, y: y + 0.4, w: w - 0.6, h: 0.3,
    fontSize: 8.5, color: C.muted, margin: 0,
  });
}

// ═══════════════════════════════════════════════════════
async function main() {
  // Pre-render all icons once to avoid re-rendering per slide
  // Map icons by name for reuse
  const iconMap = {
    brain: [FaBrain, `#${C.white}`],
    file: [FaFileAlt, `#${C.white}`],
    lock: [FaLock, `#${C.white}`],
    pen: [FaPen, `#${C.white}`],
    robot: [FaRobot, `#${C.white}`],
    chartBar: [FaChartBar, `#${C.white}`],
    desktop: [FaDesktop, `#${C.white}`],
    project: [FaProjectDiagram, `#${C.white}`],
    chartLine: [FaChartLine, `#${C.white}`],
    bolt: [FaBolt, `#${C.white}`],
    shield: [FaShieldAlt, `#${C.white}`],
    handshake: [FaHandshake, `#${C.white}`],
    clock: [FaClock, `#${C.white}`],
    users: [FaUsers, `#${C.white}`],
    filter: [FaFilter, `#${C.white}`],
    check: [FaCheckCircle, `#${C.white}`],
    times: [FaTimesCircle, `#${C.white}`],
    cogs: [FaCogs, `#${C.white}`],
    search: [FaSearch, `#${C.white}`],
    network: [FaNetworkWired, `#${C.white}`],
  };

  const ic = {};
  for (const [key, [Icon, color]] of Object.entries(iconMap)) {
    ic[key] = await iconToBase64Png(Icon, color);
  }

  let pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Team";
  pres.title = "Presentation Title";

  // ══ SLIDE 1: COVER (dark) ══
  {
    const s = pres.addSlide();
    s.background = { color: C.dark };
    s.addShape("oval", { x: -1.2, y: -1.2, w: 4, h: 4, fill: { color: C.blue, transparency: 85 } });
    s.addShape("oval", { x: 7.5, y: 2.8, w: 3.5, h: 3.5, fill: { color: C.purple, transparency: 85 } });
    s.addText("KICKER TEXT", {
      x: 0.5, y: 1.4, w: 9, h: 0.35,
      fontSize: 12, color: "7C8DB5", fontFace: "Arial", charSpacing: 3, align: "center", margin: 0,
    });
    s.addText("Title", {
      x: 1, y: 1.8, w: 8, h: 1.0,
      fontSize: 48, bold: true, color: C.white, fontFace: "Arial", align: "center", margin: 0,
    });
    s.addText("Subtitle", {
      x: 1, y: 2.7, w: 8, h: 0.45,
      fontSize: 18, color: "94A3B8", fontFace: "Arial", align: "center", margin: 0,
    });
    addSlideNum(s, 1);
  }

  // ══ SLIDE 2: THREE CARDS (pain points) ══
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    pageTitle(s, "Section Title", 2);
    const cards = [
      { color: C.orange, icon: ic.filter, title: "Card 1", desc: "Description." },
      { color: C.orange, icon: ic.network, title: "Card 2", desc: "Description." },
      { color: C.orange, icon: ic.clock, title: "Card 3", desc: "Description." },
    ];
    cards.forEach((c, i) => {
      addCard(s, 0.35 + i * 3.2, 1.1, 3.0, 3.7, c.color, c.icon, c.title, c.desc);
    });
  }

  // ══ SLIDE 3: FLOW CHART + TECH CARDS ══
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    pageTitle(s, "Flow Chart Slide", 3);
    // Add flow nodes with arrow connectors, tech cards below
    // (customize for your content)
  }

  // ══ SLIDE 4: DUAL ENGINE ══
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    pageTitle(s, "Dual Engine Architecture", 4);
    // Left engine (blue bg), right engine (purple bg)
  }

  // ══ SLIDE 7: SWIMLANE ARCHITECTURE ══
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    pageTitle(s, "Agent Architecture", 7);
    // Layer 1: 调度层 (dark bg strip)
    // Layer 2 left: 审阅链 (blue bg), right: 拓客链 (purple bg)
    // Layer 3: 汇聚层 (green bg)
    // Layer 4: 输出层 (light bg)
    // Use agentCard() for individual agent boxes
  }

  // ══ SLIDE 8: 2×2 VALUE GRID ══
  {
    const s = pres.addSlide();
    s.background = { color: C.white };
    pageTitle(s, "Value Proposition", 8);
    // Cards with left-side accent bars instead of top bars
  }

  // ══ SLIDE 9: CLOSING (dark) ══
  {
    const s = pres.addSlide();
    s.background = { color: C.dark };
    s.addText("Key Numbers Row", {
      x: 1.5, y: 2.8, w: 7, h: 0.55,
      fontSize: 30, bold: true, color: "38BDF8", fontFace: "Arial", align: "center", margin: 0,
    });
    addSlideNum(s, 9);
  }

  await pres.writeFile({ fileName: "output.pptx" });
  console.log("Done: output.pptx");
}

main().catch(e => { console.error(e); process.exit(1); });
