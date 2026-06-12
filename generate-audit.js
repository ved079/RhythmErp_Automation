const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat,
  TabStopType, TabStopPosition, UnderlineType
} = require('docx');
const fs = require('fs');

// ── Colour palette ──────────────────────────────────────────────────────────
const C = {
  brand:   "C0003E",  // Newmi red
  dark:    "1A1A2E",  // near-black navy
  mid:     "4A4A6A",  // body text
  accent:  "E8F4FD",  // pale blue table header bg
  light:   "F8F9FA",  // alternating row
  white:   "FFFFFF",
  red:     "C0003E",
  orange:  "E67E22",
  green:   "27AE60",
  border:  "CCCCCC",
};

// ── Content width (A4, 1-inch margins each side) ────────────────────────────
const W = 9026;

// ── Border helper ────────────────────────────────────────────────────────────
const b = (color = C.border) => ({ style: BorderStyle.SINGLE, size: 1, color });
const borders = (color = C.border) => ({ top: b(color), bottom: b(color), left: b(color), right: b(color) });
const cellPad = { top: 100, bottom: 100, left: 140, right: 140 };

// ── Text helpers ─────────────────────────────────────────────────────────────
const run  = (text, opts = {}) => new TextRun({ text, font: "Arial", size: 20, color: C.mid, ...opts });
const bold = (text, opts = {}) => run(text, { bold: true, ...opts });
const para = (children, opts = {}) => new Paragraph({ children: Array.isArray(children) ? children : [children], spacing: { after: 120 }, ...opts });
const hpara = (text, level, color = C.dark, spaceAfter = 160) =>
  new Paragraph({
    heading: level,
    spacing: { before: 200, after: spaceAfter },
    children: [new TextRun({ text, font: "Arial", bold: true,
      size: level === HeadingLevel.HEADING_1 ? 36 : level === HeadingLevel.HEADING_2 ? 28 : 24,
      color })],
  });

// ── Cell helpers ─────────────────────────────────────────────────────────────
const hCell = (text, w, bg = C.accent) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  borders: borders(C.border),
  shading: { fill: bg, type: ShadingType.CLEAR },
  margins: cellPad,
  verticalAlign: VerticalAlign.CENTER,
  children: [new Paragraph({ children: [bold(text, { color: C.dark, size: 18 })], spacing: { after: 0 } })],
});
const dCell = (text, w, bg = C.white, textColor = C.mid, isBold = false) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  borders: borders(C.border),
  shading: { fill: bg, type: ShadingType.CLEAR },
  margins: cellPad,
  verticalAlign: VerticalAlign.TOP,
  children: [new Paragraph({ children: [run(text, { color: textColor, bold: isBold, size: 18 })], spacing: { after: 0 } })],
});
const rCell = (text, w, bg = C.white, textColor = C.mid) => dCell(text, w, bg, textColor);

// ── Severity badge via text color ────────────────────────────────────────────
const sevCell = (text, w) => {
  const color = text === "CRITICAL" ? "C0003E" : text === "HIGH" ? "E67E22" : text === "MEDIUM" ? "2980B9" : "27AE60";
  return dCell(text, w, C.white, color, true);
};

// ── Divider line ─────────────────────────────────────────────────────────────
const divider = (color = C.brand) => new Paragraph({
  spacing: { before: 80, after: 80 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color, space: 1 } },
  children: [],
});

// ── Bullet ───────────────────────────────────────────────────────────────────
const bullet = (text, indent = 720) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  spacing: { after: 80 },
  children: [run(text)],
});

// ── Page break ───────────────────────────────────────────────────────────────
const pageBreak = () => new Paragraph({ children: [new TextRun({ break: 1 })] });

// ════════════════════════════════════════════════════════════════════════════
//  COVER PAGE
// ════════════════════════════════════════════════════════════════════════════
const coverPage = [
  new Paragraph({ spacing: { before: 2000, after: 0 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: C.brand, space: 6 } },
    children: [new TextRun({ text: "NEWMI CARE", font: "Arial", size: 64, bold: true, color: C.brand })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [new TextRun({ text: "Candidate Assignment — Complete Submission", font: "Arial", size: 28, color: C.mid })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
    children: [new TextRun({ text: "newmi.in  |  Gurgaon, India  |  June 2026", font: "Arial", size: 22, color: C.mid, italics: true })],
  }),
  new Paragraph({ spacing: { before: 200, after: 200 }, children: [] }),
  // Task cards as simple paragraphs
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [new TextRun({ text: "TASK 1", font: "Arial", size: 24, bold: true, color: C.brand })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
    children: [new TextRun({ text: "SEO + GEO (AI Visibility) Audit", font: "Arial", size: 28, bold: true, color: C.dark })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [new TextRun({ text: "TASK 2", font: "Arial", size: 24, bold: true, color: C.brand })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 600 },
    children: [new TextRun({ text: "AI-Powered Growth Operations System", font: "Arial", size: 28, bold: true, color: C.dark })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [new TextRun({ text: "Prepared: June 2026  |  Confidential — Candidate Submission", font: "Arial", size: 20, color: C.mid, italics: true })],
  }),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  TABLE OF CONTENTS  (manual)
// ════════════════════════════════════════════════════════════════════════════
const tocPage = [
  hpara("Contents", HeadingLevel.HEADING_1, C.brand),
  divider(),
  ...[
    ["TASK 1: SEO + GEO (AI Visibility) Audit", ""],
    ["  Executive Summary & Seven Critical Findings", ""],
    ["  Part 1 — Technical SEO Audit", ""],
    ["  Part 2 — Google Presence", ""],
    ["  Part 3 — Google Business Profile", ""],
    ["  Part 4 — AI Discoverability: Per-Platform Breakdown", ""],
    ["  Part 5 — Content Audit", ""],
    ["  Part 6 — Authority & Backlink Signals", ""],
    ["  Part 7 — Competitor Benchmarking", ""],
    ["  Part 8 — Priority Recommendations", ""],
    ["TASK 2: AI-Powered Growth Operations System", ""],
    ["  Part 1 — Research: Ryze AI vs Claude + MCP", ""],
    ["  Part 2 — Newmi AI Use Cases (6 Areas)", ""],
  ].map(([title]) =>
    new Paragraph({
      spacing: { after: 100 },
      children: [run(title, { color: title.startsWith("TASK") ? C.brand : C.dark, bold: title.startsWith("TASK"), size: 20 })],
    })
  ),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  TASK 1 HEADER
// ════════════════════════════════════════════════════════════════════════════
const task1Header = [
  new Paragraph({
    spacing: { after: 60 },
    shading: { fill: C.brand, type: ShadingType.CLEAR },
    children: [new TextRun({ text: "  TASK 1: SEO + GEO (AI Visibility) Audit", font: "Arial", size: 32, bold: true, color: C.white })],
  }),
  new Paragraph({ spacing: { after: 200 }, children: [run("newmi.in  |  Gurgaon, India  |  Audit prepared June 2026", { italics: true })] }),
];

// ════════════════════════════════════════════════════════════════════════════
//  EXECUTIVE SUMMARY
// ════════════════════════════════════════════════════════════════════════════
const executiveSummary = [
  hpara("Executive Summary", HeadingLevel.HEADING_1, C.dark),
  divider(),
  para([run("Newmi Care has "), bold("strong brand recognition, excellent third-party backlinks, and impressive clinical presence"), run(" across the Delhi-NCR region — but its digital discoverability is critically broken. The website is effectively invisible to both Google and every AI search engine for all five core service queries. This report identifies seven structural issues causing this invisibility and provides a prioritised, effort-rated action plan to fix them.")]),
  new Paragraph({ spacing: { after: 200 }, children: [] }),
  hpara("Seven Critical Findings", HeadingLevel.HEADING_2, C.brand),
  ...[
    ["CRITICAL 1", "Blog and dynamic content is invisible to search engines. Newmi's website is a Next.js application that serves blog posts, clinic listings, testimonials, and statistics entirely via client-side JavaScript. Googlebot and AI crawlers see blank pages. This single issue is the root cause of near-zero organic ranking."],
    ["CRITICAL 2", "Newmi does not rank for a single commercial keyword. Searches for 'best gynaecologist in Gurgaon', 'PCOS treatment Gurgaon', 'fertility clinic Gurgaon', 'paediatrician Gurgaon', and 'women's health clinic Gurgaon' return zero results from newmi.in. Cloudnine, CK Birla, Apollo Cradle, and Birla Fertility own all top positions."],
    ["CRITICAL 3", "The most valuable SEO landing page is a 404. The URL /page/obstetrics-and-gynecology-clinic-in-gurgaon — previously indexed by Google — now returns a 404 error. A second URL /en/page/best-gynecologist-in-gurgaon also returns 404. These are Newmi's only geo-targeted SEO pages. Both are broken."],
    ["CRITICAL 4", "Google Business Profile is unclaimed or completely unoptimised. No verified Google Maps reviews exist for any Newmi clinic. Justdial shows 62 reviews at 4.9/5 and HexaHealth shows 96 ratings at 4.6/5 — but none of this reaches Google, which is the primary local ranking signal."],
    ["CRITICAL 5", "Blog content is fragmented across three subdomains. Posts live on shop.newmi.in/en/blog and care.newmi.in/en/blog while navigation links to newmi.in/blog, which returns 502 errors. All existing blog content is generating zero SEO value."],
    ["CRITICAL 6", "Zero schema/structured data markup. No MedicalClinic, Physician, MedicalCondition, FAQPage, or AggregateRating schema exists anywhere on the site. Schema is the primary mechanism by which AI engines classify an entity as a healthcare provider."],
    ["CRITICAL 7", "Newmi is completely absent from AI-generated answers. ChatGPT, Gemini, Perplexity, and Google AI Overviews do not mention Newmi for any women's health or paediatric query in Gurgaon. When searched directly, AI responses are vague, contain wrong address data, and omit all key differentiators."],
  ].map(([label, text]) =>
    new Paragraph({
      spacing: { after: 120 },
      children: [bold(label + " — ", { color: C.red }), run(text)],
    })
  ),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  PART 1: TECHNICAL SEO
// ════════════════════════════════════════════════════════════════════════════
const part1 = [
  hpara("Part 1: Technical SEO Audit", HeadingLevel.HEADING_1, C.dark),
  divider(),

  hpara("1.1  Raw Page Data — Titles, Meta Descriptions & H1 Tags", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2200, 2200, 2426, 2200],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Page URL", 2200), hCell("Title Tag", 2200), hCell("Meta Description", 2426), hCell("H1 Tag", 2200)] }),
      ...([
        ["/", "Home | Newmi Care | Newmi Care ⚠", "173 chars — over limit; no location keyword", "Prioritising Women Health"],
        ["/clinics", "Clinics | Newmi Care | Newmi Care ⚠", "MISSING", "Prioritising Women Health (duplicate)"],
        ["/about-us", "About Us | Newmi Care | Newmi Care ⚠", "113 chars", "About Newmi Care"],
        ["/blog", "Blog | Newmi Care | Newmi Care ⚠", "MISSING", "MISSING"],
        ["/blog/[post]", "Blog Post | Newmi Care (generic)", "38 chars — critically generic", "MISSING on all posts"],
        ["/care-plans", "Care Plans | Newmi Care | Newmi Care ⚠", "151 chars", "Women Health Care Plans"],
        ["/page/obstetrics-...", "404 fallback", "Generic fallback", "404 — Page Not Found"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2200,2200,2426,2200][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 200 }, children: [] }),

  hpara("1.2  Technical SEO Issue Master Table", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2800, 4326, 1900],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Page", 2800), hCell("Issue", 4326), hCell("Severity", 1900)] }),
      ...([
        ["All pages", "Title tag duplicates 'Newmi Care' twice — zero location/service keywords", "HIGH"],
        ["Homepage", "Meta description 173 chars (over 160 limit); no location or service keyword", "HIGH"],
        ["Homepage", "H1 has no geo or service keywords: 'Prioritising Women Health'", "HIGH"],
        ["Homepage + Blog", "Statistics, testimonials, clinic listings, all blog content NOT server-side rendered — invisible to Googlebot", "CRITICAL"],
        ["/clinics", "All clinic location data JavaScript-rendered — addresses uncrawlable", "CRITICAL"],
        ["Blog", "Fragmented across 3 subdomains with 502 errors on listing pages", "CRITICAL"],
        ["Blog posts", "Article body content not SSR'd — 0 words indexed per post", "CRITICAL"],
        ["Blog posts", "Generic title 'Blog Post | Newmi Care' — no article title in <title>", "CRITICAL"],
        ["Blog posts", "No author name or publish date — E-E-A-T failure (YMYL health content)", "CRITICAL"],
        ["/page/obstetrics-...", "404 error — primary geo-keyword landing page broken", "CRITICAL"],
        ["/en/page/best-gynecologist-...", "404 error — second geo landing page broken", "CRITICAL"],
        ["All pages", "Zero schema markup — no MedicalClinic, Physician, FAQPage, AggregateRating", "HIGH"],
        ["Homepage", "Canonical: https://newmi.in (non-www) conflicts with www redirect", "MEDIUM"],
        ["robots.txt", "/careers, /influencer-program, /pregnancy-care-plan blocked — unintentional", "MEDIUM"],
        ["robots.txt", "Disallow contradicts index,follow meta tags on /careers and /influencer-program", "HIGH"],
        ["/about-us", "H2 misspelling: 'Affordibility' instead of 'Affordability'", "MEDIUM"],
        ["/care-plans", "H2 rendering bug: 'FeedbackWhat People SayWhat People Say'", "MEDIUM"],
      ].map((row, i) => new TableRow({
        children: [
          rCell(row[0], 2800, i % 2 === 0 ? C.white : C.light),
          rCell(row[1], 4326, i % 2 === 0 ? C.white : C.light),
          sevCell(row[2], 1900),
        ],
      }))),
    ],
  }),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  PART 2: GOOGLE PRESENCE
// ════════════════════════════════════════════════════════════════════════════
const part2 = [
  hpara("Part 2: Google Presence Findings", HeadingLevel.HEADING_1, C.dark),
  divider(),

  hpara("2.1  Index Status", HeadingLevel.HEADING_2),
  para([run("A "), bold("site:newmi.in"), run(" search returns approximately 5–10 indexed pages from the main domain. The sitemap.xml lists only 7 URLs — extremely thin for a healthcare brand that should have 50+ indexed pages. Subdomains (shop.newmi.in, care.newmi.in) surface before the main domain, indicating they are cannibalising what little domain authority exists.")]),

  hpara("2.2  Keyword Rankings", HeadingLevel.HEADING_2),
  para([bold("KEY FINDING — ", { color: C.red }), run("Newmi Care does not appear in the top 10 results for a single commercial service keyword.")]),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2600, 1500, 3026, 1900],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Search Query", 2600), hCell("Newmi?", 1500), hCell("Top 3 Competitors", 3026), hCell("Notes", 1900)] }),
      ...([
        ["Best gynaecologist in Gurgaon", "NO", "Cloudnine, Max Hospital, CK Birla", "Local Pack + Practo dominate"],
        ["PCOS treatment Gurgaon", "NO", "CK Birla, Birla Fertility, CIFAR IVF", "Specialist clinic pages rank"],
        ["Fertility clinic Gurgaon", "NO", "Nova IVF, Cloudnine, Birla Fertility", "IVF chains dominate"],
        ["Women's health clinic Gurgaon", "NO", "Practo, Wellstar, Well Woman Clinic", "Directories + local clinics"],
        ["Paediatrician Gurgaon", "NO", "Cloudnine, Medanta, Apollo Cradle", "Hospital chains + Practo"],
        ["Newmi Care (brand)", "YES — #1", "App Store, LinkedIn, Play Store", "No Knowledge Panel visible"],
      ].map((row, i) => new TableRow({
        children: [
          rCell(row[0], 2600, i % 2 === 0 ? C.white : C.light),
          rCell(row[1], 1500, i % 2 === 0 ? C.white : C.light, row[1] === "NO" ? C.red : C.green),
          rCell(row[2], 3026, i % 2 === 0 ? C.white : C.light),
          rCell(row[3], 1900, i % 2 === 0 ? C.white : C.light),
        ],
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  hpara("2.3  Google Knowledge Panel", HeadingLevel.HEADING_2),
  para([run("No Google Knowledge Panel exists for Newmi Care. This indicates insufficient structured data and entity recognition by Google. A Knowledge Panel would provide free above-fold brand visibility for all branded searches and is achievable through schema markup + a Wikidata entry.")]),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  PART 3: GBP
// ════════════════════════════════════════════════════════════════════════════
const part3 = [
  hpara("Part 3: Google Business Profile Analysis", HeadingLevel.HEADING_1, C.dark),
  divider(),
  para([bold("CRITICAL GAP — ", { color: C.red }), run("No confirmed, claimed, and optimised Google Business Profile exists for any Newmi clinic location. This single gap explains why Newmi cannot appear in the Google Local Pack — the top 3 map results that dominate above-fold for every local healthcare query.")]),

  hpara("3.1  Clinic Locations & Review Status", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2200, 2500, 1576, 1576, 1174],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Location", 2200), hCell("Address", 2500), hCell("Google Reviews", 1576), hCell("3rd Party Reviews", 1576), hCell("GBP Status", 1174)] }),
      ...([
        ["Gurgaon — Sector 69", "Shop 150 & 158, 1F, Spaze Corporate Park", "NONE confirmed", "JustDial: 4.9/5, 62 reviews", "Unclaimed"],
        ["Gurgaon — Sector 57", "LG 08, Bestech Central Square Mall", "NONE confirmed", "Practo: low volume", "Unclaimed"],
        ["Gurgaon — Sector 102", "Shop 33, 1F, Suncity Avenue-102", "NONE confirmed", "0 visible reviews", "Unclaimed"],
        ["Noida — Sector 49", "Not fully confirmed", "NONE confirmed", "HexaHealth: 4.6/5, 96 ratings", "Unclaimed"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2200,2500,1576,1576,1174][j], i % 2 === 0 ? C.white : C.light, j === 2 ? C.red : C.mid)),
      }))),
    ],
  }),

  new Paragraph({ spacing: { after: 160 }, children: [] }),
  hpara("3.2  The Review Gap Opportunity", HeadingLevel.HEADING_2),
  para([run("JustDial already shows "), bold("62 reviews at 4.9/5"), run(" and HexaHealth shows "), bold("96 ratings at 4.6/5."), run(" Patients are clearly willing to leave positive reviews. None of this social proof is reaching Google. Redirecting even 20% of post-visit review activity to Google would produce a measurable Local Pack ranking uplift within 60 days.")]),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  PART 4: AI DISCOVERABILITY — PER-PLATFORM
// ════════════════════════════════════════════════════════════════════════════
const part4 = [
  hpara("Part 4: AI Discoverability — Per-Platform Analysis", HeadingLevel.HEADING_1, C.dark),
  divider(),
  para([run("GEO tests were conducted across ChatGPT, Gemini, Perplexity, and Google AI Overviews for five commercial queries and one direct brand search. Actual AI responses were collected and analysed.")]),
  new Paragraph({ spacing: { after: 100 }, children: [bold("GEO Readiness Score: ", { color: C.red }), run("2 / 10 — Zero presence in AI-generated answers for all commercial queries.")] }),

  hpara("4.1  AI Query Test Results — Overview", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2400, 1300, 1300, 1300, 1300, 1426],
    rows: [
      new TableRow({ tableHeader: true, children: [
        hCell("Query", 2400), hCell("ChatGPT", 1300), hCell("Gemini", 1300), hCell("Perplexity", 1300), hCell("Google AIO", 1300), hCell("Top Cited", 1426)
      ]}),
      ...([
        ["Best Gynaecologist in Gurgaon", "NO", "NO", "NO", "NO", "Cloudnine, Max, CK Birla"],
        ["PCOS treatment Gurgaon", "NO", "NO", "NO", "NO", "CK Birla, CIFAR IVF"],
        ["Fertility clinic Gurgaon", "NO", "NO", "NO", "NO", "Nova IVF, Indira IVF"],
        ["Paediatrician near me", "NO", "NO", "NO", "NO", "Cloudnine, Medanta"],
        ["Women's health clinic Gurgaon", "NO", "NO", "NO", "NO", "Fortis, Columbia Asia"],
        ["Newmi Care (direct)", "YES*", "YES*", "YES*", "YES*", "Poor quality — see 4.3"],
      ].map((row, i) => new TableRow({
        children: [
          rCell(row[0], 2400, i % 2 === 0 ? C.white : C.light),
          rCell(row[1], 1300, i % 2 === 0 ? C.white : C.light, row[1] === "NO" ? C.red : C.green),
          rCell(row[2], 1300, i % 2 === 0 ? C.white : C.light, row[2] === "NO" ? C.red : C.green),
          rCell(row[3], 1300, i % 2 === 0 ? C.white : C.light, row[3] === "NO" ? C.red : C.green),
          rCell(row[4], 1300, i % 2 === 0 ? C.white : C.light, row[4] === "NO" ? C.red : C.green),
          rCell(row[5], 1426, i % 2 === 0 ? C.white : C.light),
        ],
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 180 }, children: [run("* Newmi Care is discoverable via direct brand search, but response quality is poor — wrong addresses, generic descriptions, and missing differentiators.", { italics: true, size: 18 })] }),

  hpara("4.2  Per-Platform Breakdown", HeadingLevel.HEADING_2),

  // ChatGPT
  para([bold("ChatGPT (GPT-4o with browsing) — ", { color: C.dark })]),
  para([run("When queried with 'Best Gynaecologist in Gurgaon', ChatGPT surfaces Cloudnine, CK Birla, and Fortis — all sourced from Practo listings and hospital websites. Newmi is absent. For the direct 'Newmi Care' query, ChatGPT delivers a reasonable overview (founding year, founders Aditi Mittal & Sanchit Agarwal, omnichannel model) but sources this primarily from LinkedIn and Inc42, not newmi.in. The service description is generic and misses all key differentiators: Care Plans, Smart OPD, the mobile app's 5.0 rating, and ABDM integration.")]),
  para([bold("Why Newmi is missing: ", { color: C.mid }), run("ChatGPT browses the web at query time and prioritises SSR'd content from high-DA domains. Newmi's client-side rendered pages return near-empty HTML, so ChatGPT cannot extract meaningful content from newmi.in.")]),

  // Gemini
  para([bold("Gemini (Google's AI with Search grounding) — ", { color: C.dark })]),
  para([run("Gemini's responses for commercial queries (gynaecologist, PCOS, fertility) are drawn directly from Google Search's top results — the same competitors that dominate traditional SERPs. Because Newmi has no indexed service pages and no Google Business Profile reviews, it does not appear in Gemini's source pool. For the direct brand query, Gemini produces a structured response describing Newmi's omnichannel model and Care Plans — but incorrectly states the clinic address as 'Sushant Lok I' rather than the correct Sector 69 and Sector 57 locations.")]),
  para([bold("Why Newmi is missing: ", { color: C.mid }), run("Gemini's AI responses are grounded in Google Search. No GBP + no indexed service pages = no Gemini visibility for commercial queries. Schema markup and Local Pack presence are the fastest levers here.")]),

  // Perplexity
  para([bold("Perplexity AI — ", { color: C.dark })]),
  para([run("Perplexity actively crawls the web and builds citations from multiple sources. For healthcare queries in Gurgaon, it cites Practo, Cloudnine, and individual clinic websites — all of which have crawlable, SSR'd content. Newmi's JavaScript-rendered pages are effectively invisible to Perplexity's crawler. For the direct brand search, Perplexity retrieves fragmented information from Practo, YourStory, and LinkedIn — but cannot extract clinic details or service descriptions from newmi.in itself. Doctor names returned are placeholders.")]),
  para([bold("Why Newmi is missing: ", { color: C.mid }), run("Perplexity weights content that is directly crawlable and citations from authoritative health directories. Newmi has neither SSR'd service pages nor health-authority backlinks. Wikipedia and Quora presence would immediately improve Perplexity citation probability.")]),

  // Google AI Overviews
  para([bold("Google AI Overviews — ", { color: C.dark })]),
  para([run("Google AI Overviews appear at the top of search results for all five test queries. They exclusively cite Cloudnine, CK Birla, Fortis, Max Hospital, and Practo — brands with complete GBP profiles, schema markup, hundreds of Google reviews, and fully crawlable service pages. The AI Overview for 'PCOS treatment Gurgaon' references a CK Birla PCOS treatment page with FAQPage schema; Newmi has no equivalent page. Google AI Overviews pull directly from the same signals used for traditional ranking: schema, E-E-A-T, GBP, and indexed content.")]),
  para([bold("Why Newmi is missing: ", { color: C.mid }), run("Google AI Overviews require the same foundational SEO elements as organic ranking. Fixing SSR, implementing schema, claiming GBP, and creating service landing pages will unlock both traditional ranking and AI Overview inclusion simultaneously.")]),

  hpara("4.3  Direct Brand Search — AI Response Quality Issues", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [3013, 3013, 3000],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Issue", 3013), hCell("What AI Engines Say", 3013), hCell("What Should Be Said", 3000)] }),
      ...([
        ["Wrong address data", "States 'Sushant Lok I' or generic Gurgaon", "Sector 69 (Spaze Corporate Park) and Sector 57 (Bestech Central Square Mall)"],
        ["Generic service description", "'Various medical services for women'", "PCOS, Fertility, Pregnancy (PregCare), Paediatrics, Smart OPD, ABDM integration"],
        ["Missing doctor names", "Placeholder names — AI could not retrieve consultants", "Named, qualified consultants visible on SSR'd doctor profile pages"],
        ["No differentiators", "Described like any generic clinic", "Care Plans (lifecycle subscriptions), Care Buddy, mobile app (5.0 rating), Rs. 12.5cr seed funding"],
        ["Source quality", "Practo, Inc42, LinkedIn cited more than newmi.in", "newmi.in should be primary citation — requires SSR and schema"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [3013,3013,3000][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  PART 5: CONTENT AUDIT
// ════════════════════════════════════════════════════════════════════════════
const part5 = [
  hpara("Part 5: Content Audit", HeadingLevel.HEADING_1, C.dark),
  divider(),

  hpara("5.1  Blog Infrastructure Issues", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [4013, 5013],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Infrastructure Issue", 4013), hCell("Status", 5013)] }),
      ...([
        ["Estimated blog posts", "35–50+ posts exist but exact count impossible due to 502 errors"],
        ["Blog fragmentation", "Content across 3 subdomains: shop.newmi.in, care.newmi.in, newmi.in"],
        ["Navigation accuracy", "Header links to care.newmi.in/en/blog but content lives on shop.newmi.in"],
        ["Author attribution", "MISSING on all posts — critical E-E-A-T failure"],
        ["Publish dates", "MISSING on all posts — Google cannot assess freshness"],
        ["Post title in <title>", "NOT used — all posts show generic 'Blog Post | Newmi Care'"],
        ["Article body SSR", "Zero — entire article content is JavaScript-rendered and uncrawlable"],
      ].map((row, i) => new TableRow({
        children: [rCell(row[0], 4013, i % 2 === 0 ? C.white : C.light), rCell(row[1], 5013, i % 2 === 0 ? C.white : C.light)],
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  hpara("5.2  Blog Content Quality (5 Posts Sampled)", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2800, 1500, 4726],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Quality Element", 2800), hCell("Status", 1500), hCell("Notes", 4726)] }),
      ...([
        ["Word count", "GOOD", "Range 1,382–1,726 words per post — long-form content exists"],
        ["Meta descriptions", "GOOD", "Well-written, keyword-rich descriptions found on sampled posts"],
        ["Internal links", "INCONSISTENT", "Range 1–9 per post (avg ~5). Some posts severely under-linked"],
        ["Author name", "MISSING", "Zero author attribution — E-E-A-T critical failure for YMYL health"],
        ["Publish date", "MISSING", "No visible dates — Google cannot assess content freshness"],
        ["H1 tag", "MISSING", "No H1 on any blog post page"],
        ["Article body (SSR)", "MISSING", "All content JS-rendered — completely uncrawlable"],
        ["BlogPosting schema", "MISSING", "No structured data on any post"],
      ].map((row, i) => new TableRow({
        children: [
          rCell(row[0], 2800, i % 2 === 0 ? C.white : C.light),
          rCell(row[1], 1500, i % 2 === 0 ? C.white : C.light, row[1] === "MISSING" ? C.red : row[1] === "GOOD" ? C.green : C.orange),
          rCell(row[2], 4726, i % 2 === 0 ? C.white : C.light),
        ],
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),
  para([bold("Key insight: ", { color: C.brand }), run("Newmi has invested in creating the right content — but because it is client-side rendered and living on subdomains, every piece of that investment is generating zero SEO return. The content exists; it just cannot be seen.")]),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  PART 6: AUTHORITY & BACKLINKS
// ════════════════════════════════════════════════════════════════════════════
const part6 = [
  hpara("Part 6: Authority & Backlink Signals", HeadingLevel.HEADING_1, C.dark),
  divider(),

  hpara("6.1  High-Authority Backlink Profile", HeadingLevel.HEADING_2),
  para([run("Newmi has a surprisingly strong backlink profile for a 3-year-old startup, driven primarily by press coverage of its Rs. 12.5 crore seed funding round.")]),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [3200, 1300, 2600, 1926],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Domain", 3200), hCell("Est. DA", 1300), hCell("Link Type", 2600), hCell("SEO Value", 1926)] }),
      ...([
        ["economictimes.indiatimes.com", "90+", "Editorial — funding news", "Very High"],
        ["entrepreneur.com", "90+", "Funding news", "Very High"],
        ["yourstory.com", "80+", "3 feature articles", "Very High"],
        ["inc42.com", "75+", "Company profile + 2 news items", "High"],
        ["crunchbase.com", "90+", "Company profile", "High"],
        ["practo.com", "75+", "5 clinic listings", "High — local SEO"],
        ["justdial.com", "80+", "9+ clinic listings across NCR", "High — local SEO"],
        ["play.google.com", "95+", "App listing", "Very High"],
        ["linkedin.com", "95+", "Company page (8,298 followers)", "Very High"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [3200,1300,2600,1926][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  hpara("6.2  Critical Missing Authority Signals", HeadingLevel.HEADING_2),
  para([bold("CRITICAL AUTHORITY GAP — ", { color: C.red }), run("Press coverage is strong but concentrated in startup/tech media (YourStory, Inc42). Zero citations from medical/health authority sources. These are the domains AI engines trust and cite for medical queries.")]),
  ...[
    "No Wikipedia page — AI engines weight Wikipedia heavily as an entity source; even a stub would boost citation probability",
    "No Wikidata entry — required for Google Knowledge Panel eligibility",
    "No government/ABDM citations despite Newmi claiming ABDM integration",
    "NAP inconsistency: 'Newmi's', 'Newmi Care's', 'Newmi Women', 'Newmi Women & Child Clinic' — fragments Google entity matching",
    "Facebook: 0 reviews / 'Not yet rated' — severely damages trust for a healthcare brand",
    "Twitter/X: 3 followers, 0 posts ever published — effectively abandoned",
  ].map(text => bullet(text)),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  PART 7: COMPETITOR BENCHMARKING
// ════════════════════════════════════════════════════════════════════════════
const part7 = [
  hpara("Part 7: Competitor Benchmarking", HeadingLevel.HEADING_1, C.dark),
  divider(),

  hpara("7.1  Side-by-Side Comparison", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [1800, 1806, 1806, 1806, 1808],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Metric", 1800), hCell("Newmi Care", 1806), hCell("Cloudnine", 1806), hCell("CK Birla", 1806), hCell("Wellstar", 1808)] }),
      ...([
        ["Title Tag", "No keywords", "Best Gynecologist in Gurgaon", "Best Hospital in Gurgaon", "Best Gynaecologist in Gurgaon"],
        ["Schema Markup", "❌ None", "✅ AggregateRating + FAQPage", "✅ MedicalOrg + Physician", "✅ MedicalClinic (best-in-class)"],
        ["Blog SSR", "❌ Client-side", "✅ Yes — active", "✅ Yes — active", "❌ Limited"],
        ["AI Visibility", "❌ Zero", "✅ Very High", "✅ Very High", "✅ Moderate"],
        ["Google Reviews", "None confirmed", "656+ (Justdial)", "Hundreds per location", "189 reviews"],
        ["Service Landing Pages", "❌ None — 404s", "✅ Per service + location", "✅ Per treatment", "✅ Per treatment"],
        ["Doctor Profile Pages", "❌ None", "✅ Full pages per doctor", "✅ Full pages per doctor", "✅ Per doctor"],
        ["GBP Optimised", "❌ No", "✅ Yes", "✅ Yes", "✅ Partial"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [1800,1806,1806,1806,1808][j], i % 2 === 0 ? C.white : C.light, j === 1 && cell.startsWith("❌") ? C.red : C.mid)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),
  para([bold("Newmi's Unleveraged Advantage: ", { color: C.brand }), run("Newmi is the ONLY clinic in this competitive set with Care Plans (lifecycle subscription healthcare), a mobile app with 5.0 rating, Smart OPD (B2B corporate wellness), and a comprehensive lifecycle approach spanning puberty to menopause. None of these differentiators appear in title tags, meta descriptions, or schema markup — meaning Google and AI engines have no way of knowing about them.")]),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  PART 8: RECOMMENDATIONS
// ════════════════════════════════════════════════════════════════════════════
const part8 = [
  hpara("Part 8: Priority Recommendations", HeadingLevel.HEADING_1, C.dark),
  divider(),

  hpara("P0 — Critical (Week 1–2)", HeadingLevel.HEADING_2, C.red),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [280, 2500, 2000, 1000, 3246],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("#", 280), hCell("Recommendation", 2500), hCell("Expected Impact", 2000), hCell("Effort", 1000), hCell("Why It Matters", 3246)] }),
      ...([
        ["1", "Fix Next.js SSR — enable server-side rendering for all blog posts, clinic listings, homepage statistics, and testimonials", "VERY HIGH — unlocks indexation of 35–50 blog posts and all clinic data in one fix", "Medium", "Root cause of near-zero organic ranking. Every other content fix is worthless until Googlebot can read the pages."],
        ["2", "Fix or 301-redirect the two broken 404 landing pages (/page/obstetrics-and-gynecology-clinic-in-gurgaon and /en/page/best-gynecologist-in-gurgaon)", "HIGH — recovers previously indexed pages", "Low — 1–2 hours", "These are Newmi's only existing geo-targeted SEO URLs. Both returning 404. Immediate fix required."],
        ["3", "Fix title tag template — remove duplicate 'Newmi Care'. Change to: 'Best Gynecologist in Gurgaon | Women's Health Clinic | Newmi Care'", "HIGH — immediate relevance signal for all commercial queries", "Low — 1 hour", "Every competitor targets primary keyword in title tag. Newmi targets nothing."],
        ["4", "Claim and optimise Google Business Profile for all 4+ clinic locations. Add photos, hours, services. Implement post-visit Google Review collection.", "VERY HIGH — enables Local Pack appearance", "Low-Medium — 1–2 days/location", "GBP is the #1 local ranking factor. Without it, Newmi cannot appear in map pack."],
        ["5", "Fix blog post meta description and title tag templates — insert article title into <title>; generate unique meta descriptions per post", "HIGH — each post becomes individually discoverable", "Low — 2–3 hours", "38-character generic meta descriptions are invisible in SERPs."],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [280,2500,2000,1000,3246][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  hpara("P1 — High Priority (Week 2–4)", HeadingLevel.HEADING_2, C.orange),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [280, 2500, 2000, 1000, 3246],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("#", 280), hCell("Recommendation", 2500), hCell("Expected Impact", 2000), hCell("Effort", 1000), hCell("Why It Matters", 3246)] }),
      ...([
        ["6", "Create 5 geo-service landing pages on newmi.in: /best-gynaecologist-gurgaon, /pcos-treatment-gurgaon, /fertility-clinic-gurgaon, /paediatrician-gurgaon, /womens-health-clinic-gurgaon. Each: 800+ words SSR'd, doctor profiles, FAQs, internal links.", "VERY HIGH — directly targets 5 core commercial queries where Newmi has zero presence", "High — 2–3 weeks", "Competitors rank because they have these pages. Newmi has none. Single biggest organic traffic opportunity."],
        ["7", "Implement schema markup: MedicalClinic on clinic pages, Physician for each doctor, FAQPage on care-plans and service pages, AggregateRating using Justdial/Practo ratings, BlogPosting on all posts", "HIGH — enables rich results, Knowledge Panel eligibility, AI citation", "Medium — 1–2 days/page type", "Schema is how AI engines classify Newmi as a healthcare provider. Without it, AI cannot do so."],
        ["8", "Migrate all blog content from shop.newmi.in/en/blog to newmi.in/blog with 301 redirects. Fix 502 errors on listing pages.", "HIGH — consolidates domain authority", "Medium — 1–2 week dev task", "Subdomains dilute authority. All content investment is wasted until it lives on the main domain."],
        ["9", "Resolve robots.txt contradictions — remove Disallow for /careers and /influencer-program OR add noindex. Unblock /pregnancy-care-plan.", "MEDIUM", "Low — 30 min", "Sends conflicting signals to Googlebot. Simple fix with disproportionate crawl efficiency benefit."],
        ["10", "Create individual doctor profile pages — qualifications, specialisation, experience, photo, booking CTA, and Physician schema.", "HIGH — doctors are searched by name; builds E-E-A-T", "Medium — 1–2 days/doctor", "Patients search for specific doctors. Every competitor has these pages. Newmi has none."],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [280,2500,2000,1000,3246][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  hpara("P2 — Medium Priority (Month 2–3)", HeadingLevel.HEADING_2, C.green),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [280, 2500, 2000, 1000, 3246],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("#", 280), hCell("Recommendation", 2500), hCell("Expected Impact", 2000), hCell("Effort", 1000), hCell("Why It Matters", 3246)] }),
      ...([
        ["11", "Standardise NAP across ALL directories — use 'Newmi Women & Child Clinic' consistently on Practo, Justdial, GBP, Facebook with identical address and phone format.", "MEDIUM", "Low — 1–2 days", "Inconsistent naming fragments Google's entity graph and weakens local ranking signals."],
        ["12", "Build a Wikipedia and Wikidata presence for Newmi Care. YourStory features and Inc42 funding coverage provide sufficient notability.", "HIGH", "Medium — 1–2 days", "AI engines (Perplexity, ChatGPT) weight Wikipedia heavily. A stub entry would measurably boost AI citation probability."],
        ["13", "Sustained PR pipeline beyond funding news — founder op-eds in TOI Health, HT Health, NDTV Health, PCOS Awareness Month campaigns, original research/surveys.", "HIGH", "High — ongoing", "Current backlinks are from startup media, not health media. AI engines trust health authority domains for medical queries."],
        ["14", "Establish Quora and Reddit presence — answer questions about gynaecology, PCOS, and paediatrics in Gurgaon with genuine helpful responses mentioning Newmi Care.", "MEDIUM", "Low — 2–3 hrs/week", "Quora and Reddit are frequently cited by AI engines as source material. Zero presence = zero AI citation from these platforms."],
        ["15", "Implement GEO monitoring using Peec AI, Otterly AI, or Profound to track AI mention frequency across ChatGPT, Gemini, Perplexity.", "Diagnostic", "Low — 1–2 hours setup", "Without measurement, impossible to know which actions are driving AI citation improvement."],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [280,2500,2000,1000,3246][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  TASK 2 HEADER
// ════════════════════════════════════════════════════════════════════════════
const task2Header = [
  new Paragraph({
    spacing: { after: 60 },
    shading: { fill: C.dark, type: ShadingType.CLEAR },
    children: [new TextRun({ text: "  TASK 2: AI-Powered Growth Operations System", font: "Arial", size: 32, bold: true, color: C.white })],
  }),
  new Paragraph({ spacing: { after: 200 }, children: [run("Research on Ryze AI and Claude + MCP, with Newmi-specific use cases across 6 growth areas.", { italics: true })] }),
];

// ════════════════════════════════════════════════════════════════════════════
//  TASK 2 PART 1: RESEARCH
// ════════════════════════════════════════════════════════════════════════════
const task2Part1 = [
  hpara("Part 1: Research — Ryze AI vs Claude + MCP", HeadingLevel.HEADING_1, C.dark),
  divider(),

  hpara("What is Ryze AI?", HeadingLevel.HEADING_2),
  para([run("Ryze AI is a purpose-built autonomous advertising platform that manages paid campaigns across Google Ads, Meta (Facebook/Instagram), LinkedIn, ChatGPT, and Perplexity from a single unified dashboard. It is designed specifically for performance marketers and agencies running significant cross-platform ad spend.")]),
  para([bold("Core capabilities:")]),
  ...[
    "Multi-platform AI management — manages campaigns across Google, Meta, LinkedIn, ChatGPT Ads, and Perplexity Ads from one interface",
    "Intelligent spend analysis — AI continuously reviews campaign data and automatically identifies wasted spend",
    "Creative generation — automatically generates new ad creatives and tests variations without manual intervention",
    "Campaign scaling — identifies winning campaigns and scales them while pausing underperformers",
    "AI Analyst — ask questions in natural language and get instant insights from campaign data",
    "Structural optimisation — fixes campaign structure issues (bid strategies, audience overlap, budget allocation) autonomously",
    "MCP integration — Ryze AI has also built a universal MCP integration allowing it to connect with external ad platforms programmatically",
  ].map(text => bullet(text)),
  para([run("Ryze AI is best described as a "), bold("plug-and-play autonomous ad operations layer"), run(" — no custom development required. It connects to your ad accounts and begins optimising immediately. Pricing starts at approximately $99/month.")]),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  hpara("What does Claude + MCP enable?", HeadingLevel.HEADING_2),
  para([run("MCP (Model Context Protocol) is an open standard created by Anthropic in November 2024 and now governed by the Linux Foundation. It acts as a universal adapter that allows Claude (and other AI models) to connect to any external tool, API, database, CRM, or ad platform via standardised server connections. As of March 2026, there are over 10,000 active public MCP servers and 97 million monthly SDK downloads.")]),
  para([bold("What this means practically:")]),
  ...[
    "Claude can connect to Google Ads, Meta Ads Manager, HubSpot CRM, Google Analytics, Notion, Slack, Gmail, and 6,000+ other tools via Zapier MCP — all in one session",
    "Instead of switching between dashboards, a marketer can type in plain English: 'Show me which campaigns had the highest CPA last week and suggest 3 optimisations' — Claude pulls the data and responds",
    "Claude can execute multi-step workflows: analyse performance → draft ad copy variations → update landing page content → send a Slack summary — all autonomously",
    "Unlike Ryze AI, Claude + MCP is not pre-built for advertising — it requires initial setup and configuration of MCP servers, and benefits from prompt engineering",
    "The payoff is a completely custom AI system that can operate across every function in a growth team: ads, SEO, CRM, reporting, lead qualification, and content",
  ].map(text => bullet(text)),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  hpara("Comparison & Recommendation for Newmi", HeadingLevel.HEADING_2),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2200, 3413, 3413],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Dimension", 2200), hCell("Ryze AI", 3413), hCell("Claude + MCP", 3413)] }),
      ...([
        ["Primary focus", "Paid advertising (Google + Meta + LinkedIn)", "Any marketing function — ads, SEO, CRM, reporting, content"],
        ["Setup required", "Low — plug-and-play connection to ad accounts", "Medium — requires MCP server configuration and prompt design"],
        ["Customisation", "Limited to advertising workflows", "Fully customisable to any business workflow"],
        ["Cross-function scope", "Ads only", "Ads + SEO + Landing Pages + Lead Qual + Reporting"],
        ["Technical barrier", "Non-technical friendly", "Low-to-medium (improves monthly as MCP tooling matures)"],
        ["Best for", "Teams scaling ad spend with limited ops bandwidth", "Teams wanting one integrated AI layer across all growth functions"],
        ["Cost model", "Monthly SaaS ($99+/month)", "Claude API cost + MCP server setup (typically lower at scale)"],
        ["AI quality", "Pre-defined ad optimization logic", "Latest Claude frontier model — reasoning, strategy, writing"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2200,3413,3413][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),
  para([bold("Recommendation for Newmi: Claude + MCP is the more relevant approach.", { color: C.brand })]),
  para([run("Here's why: Newmi's core problem is not just ad optimisation — it's a "), bold("full-stack growth operations gap"), run(". The brand needs SEO infrastructure built, content created, lead qualification systematised, GBP and schema implemented, and reporting set up from near-zero. Ryze AI solves only the paid ads slice of this. Claude + MCP can serve as a unified AI growth layer that handles all six areas simultaneously — ads, SEO/GEO, landing pages, lead qualification, and reporting — all connected to Newmi's actual tools (Google Ads, Meta, HubSpot/Zoho CRM, Google Analytics) via a single interface.")]),
  para([run("That said, the two are not mutually exclusive. A practical approach for Newmi would be to "), bold("use Claude + MCP as the primary intelligence and workflow layer"), run(", and consider Ryze AI as a plug-in for autonomous bid optimisation once ad spend grows to a level that justifies dedicated tooling.")]),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  TASK 2 PART 2: USE CASES
// ════════════════════════════════════════════════════════════════════════════
const task2Part2 = [
  hpara("Part 2: Newmi AI Use Cases Across 6 Growth Areas", HeadingLevel.HEADING_1, C.dark),
  divider(),
  para([run("The following use cases are mapped specifically to Newmi's current situation: near-zero organic visibility, unclaimed GBP, client-side rendered website, limited ops team, and a strong but underutilised content and brand asset base.")]),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  // ── 1. Google Ads
  hpara("1. Google Ads", HeadingLevel.HEADING_2, C.dark),
  para([bold("Current situation: ", { color: C.mid }), run("Newmi likely runs limited Google Ads, but without SSR'd landing pages, ads are sending paid traffic to pages that return generic or broken content — wasting every rupee spent.")]),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2800, 3313, 2913],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Use Case", 2800), hCell("What AI Does", 3313), hCell("Tool / Approach", 2913)] }),
      ...([
        ["Campaign performance analysis", "Claude pulls Google Ads data via MCP, identifies high-CPA campaigns, wasted spend on broad match keywords, and low-QS ads — delivers a weekly priority list in plain English", "Claude + Google Ads MCP"],
        ["Ad copy generation & testing", "Given target keyword ('PCOS treatment Gurgaon') and landing page content, Claude generates 5 RSA headline variations and 3 descriptions optimised for intent. A/B tests tracked via MCP.", "Claude + Google Ads MCP"],
        ["Keyword gap identification", "Claude compares Newmi's current keyword list against competitor ads (CK Birla, Cloudnine) scraped via search, and identifies high-intent gaps not being targeted", "Claude + web search MCP"],
        ["Negative keyword management", "Claude analyses search term reports weekly and auto-suggests negative keywords to prevent budget waste on irrelevant queries (e.g. 'free', 'government', 'nursing jobs')", "Claude + Google Ads MCP"],
        ["Campaign brief generation", "When a new service page goes live (e.g. /fertility-clinic-gurgaon), Claude auto-generates the corresponding Google Ads campaign brief: campaign structure, match types, ad groups, and copy", "Claude standalone"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2800,3313,2913][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  // ── 2. Meta Ads
  hpara("2. Meta Ads", HeadingLevel.HEADING_2, C.dark),
  para([bold("Current situation: ", { color: C.mid }), run("Newmi has 11,000 Instagram followers and 956 posts — strong creative raw material. Meta Ads are likely underutilised as a performance channel and could be a fast-growing acquisition channel for PCOS, pregnancy, and postpartum care queries.")]),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2800, 3313, 2913],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Use Case", 2800), hCell("What AI Does", 3313), hCell("Tool / Approach", 2913)] }),
      ...([
        ["Creative fatigue detection", "Claude monitors CTR and frequency data via Meta MCP — flags ads with rising frequency and declining CTR; triggers brief for new creative before ROAS drops", "Claude + Meta Ads MCP"],
        ["Audience segmentation briefs", "For each care journey (PCOS, fertility, pregnancy), Claude drafts a Meta audience segmentation brief: interest stacks, lookalikes from existing patient list, exclusions", "Claude + Meta Ads MCP"],
        ["Instagram-to-ad repurposing", "Claude reviews top-performing organic Instagram Reels (by saves/shares), identifies which can be repurposed as paid ads, and writes the paid overlay copy for each", "Claude + Instagram data"],
        ["Campaign copy for each funnel stage", "Claude generates TOF (awareness), MOF (consideration), and BOF (conversion) ad copy sets for each service — PCOS, fertility, paediatrics — tailored to different audience temperatures", "Claude standalone"],
        ["Budget allocation recommendation", "Given total monthly Meta budget, Claude analyses historical ROAS by campaign type and recommends optimal split across care categories", "Claude + Meta Ads MCP"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2800,3313,2913][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  // ── 3. Landing Pages
  hpara("3. Landing Pages", HeadingLevel.HEADING_2, C.dark),
  para([bold("Current situation: ", { color: C.mid }), run("Zero dedicated service or geo landing pages exist on newmi.in. This is the single biggest gap blocking both organic ranking and paid ad performance. Every rupee spent on Google Ads is landing on a client-side rendered homepage with a generic H1.")]),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2800, 3313, 2913],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Use Case", 2800), hCell("What AI Does", 3313), hCell("Tool / Approach", 2913)] }),
      ...([
        ["Service landing page drafts", "Claude drafts each of the 5 priority landing pages (/pcos-treatment-gurgaon, etc.) — 800+ words, keyword-integrated H1/H2s, FAQs, internal link suggestions, and schema markup JSON-LD to paste in", "Claude standalone"],
        ["CTA and form copy optimisation", "Claude A/B tests booking CTA copy: 'Book Appointment' vs 'Talk to a Doctor Today' vs 'Check Availability Near You' — tailors by page intent and service type", "Claude standalone"],
        ["Landing page quality scoring", "Claude reviews each landing page for SEO quality (keyword coverage, E-E-A-T signals, schema presence, CTA strength) and produces a scored checklist before publishing", "Claude standalone"],
        ["Post-SSR-fix content audit", "Once SSR is fixed, Claude auto-crawls all blog posts via fetch tools, scores each for SEO quality, and produces a prioritised optimisation backlog sorted by traffic potential", "Claude + web fetch MCP"],
        ["Personalised landing pages for ads", "For each Meta or Google ad set (e.g. PCOS campaign targeting 25–35 women), Claude drafts a matching landing page variant with audience-specific messaging", "Claude standalone"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2800,3313,2913][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  // ── 4. SEO / GEO
  hpara("4. SEO / GEO", HeadingLevel.HEADING_2, C.dark),
  para([bold("Current situation: ", { color: C.mid }), run("As documented in Task 1, Newmi's SEO and GEO infrastructure is near-zero. AI can automate the execution of the entire P0–P2 recommendation roadmap — from schema generation to content creation to GEO monitoring.")]),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2800, 3313, 2913],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Use Case", 2800), hCell("What AI Does", 3313), hCell("Tool / Approach", 2913)] }),
      ...([
        ["Schema markup generation", "Claude generates ready-to-paste JSON-LD schema blocks for every page type: MedicalClinic (clinic pages), Physician (doctor profiles), FAQPage (care plans), BlogPosting (blog posts)", "Claude standalone"],
        ["SEO content calendar", "Claude analyses keyword gaps vs competitors, maps them to content types (blog, landing page, FAQ), and builds a 3-month content calendar with target keywords, intent, and word count targets", "Claude + web search MCP"],
        ["GEO content optimisation", "Claude rewrites existing blog posts to be GEO-ready: adds cited statistics, expert quotes, FAQ sections, and entity-rich language that AI engines prefer to cite", "Claude standalone"],
        ["GEO monitoring & reporting", "Claude connects to Peec AI or Otterly AI via MCP and produces a weekly GEO report: how often Newmi is cited across ChatGPT, Gemini, Perplexity, and Google AIO, vs competitors", "Claude + GEO monitoring MCP"],
        ["Wikipedia & Wikidata entry drafting", "Claude drafts a Wikipedia-style neutral entry for Newmi Care using existing press coverage (YourStory, Inc42) as citations — ready for submission", "Claude standalone"],
        ["Technical SEO audit automation", "Claude crawls newmi.in monthly via fetch tools, compares against previous audit, and flags any new technical regressions (broken pages, missing schema, new 404s)", "Claude + web fetch MCP"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2800,3313,2913][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  // ── 5. Lead Qualification
  hpara("5. Lead Qualification", HeadingLevel.HEADING_2, C.dark),
  para([bold("Current situation: ", { color: C.mid }), run("Newmi operates a Care Buddy model where leads are paired with a dedicated care manager. AI can dramatically reduce the time burden on Care Buddies by pre-qualifying, triaging, and personalising the first touchpoint before human handoff.")]),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2800, 3313, 2913],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Use Case", 2800), hCell("What AI Does", 3313), hCell("Tool / Approach", 2913)] }),
      ...([
        ["Intake form triage", "When a lead submits a consultation request, Claude reads the form (condition, location, urgency), classifies by care category (PCOS/fertility/pregnancy/paediatrics), and assigns to the appropriate specialist — reducing manual triage by Care Buddies", "Claude + CRM MCP (HubSpot/Zoho)"],
        ["Lead scoring", "Claude analyses lead signals (referral source, query type, city, plan interest) and scores each lead 1–10 for conversion likelihood — prioritising Care Buddy outreach", "Claude + CRM MCP"],
        ["Personalised first-response messages", "Claude generates a personalised WhatsApp/email first response for each lead based on their specific health concern, name, and city — no generic templates", "Claude + WhatsApp/email MCP"],
        ["Re-engagement campaigns", "Claude identifies cold leads in the CRM (no activity in 14+ days) and drafts personalised re-engagement messages referencing their original health query", "Claude + CRM MCP"],
        ["FAQ pre-qualification bot", "Claude powers a website FAQ bot that answers common pre-consultation questions (pricing, availability, services) and captures intent signals before booking", "Claude API (embedded)"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2800,3313,2913][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 160 }, children: [] }),

  // ── 6. Reporting & Insights
  hpara("6. Reporting & Insights", HeadingLevel.HEADING_2, C.dark),
  para([bold("Current situation: ", { color: C.mid }), run("With zero current organic ranking and emerging paid presence, Newmi needs a reporting system that connects all channels and turns raw data into actionable weekly decisions — without requiring a full-time data analyst.")]),
  new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: [2800, 3313, 2913],
    rows: [
      new TableRow({ tableHeader: true, children: [hCell("Use Case", 2800), hCell("What AI Does", 3313), hCell("Tool / Approach", 2913)] }),
      ...([
        ["Weekly growth dashboard narrative", "Claude pulls data from Google Analytics, Google Ads, Meta Ads, and CRM via MCP every Monday, and writes a 300-word plain-English narrative: what grew, what dropped, what to do this week", "Claude + GA4/Ads/CRM MCP"],
        ["Cohort and funnel analysis", "Claude analyses the patient acquisition funnel (ad click → landing page → consultation → Care Plan purchase) and identifies the biggest drop-off point with suggested fixes", "Claude + GA4 MCP"],
        ["Competitor tracking", "Claude runs weekly searches for competitor ads, new content, and keyword movements; produces a monthly competitor intelligence brief", "Claude + web search MCP"],
        ["SEO progress tracking", "Claude monitors ranking position changes for all 15 target keywords weekly and produces a simple ranking velocity report: what moved, what needs attention", "Claude + Search Console MCP"],
        ["Board/investor reporting", "Claude assembles the monthly growth report from raw data — traffic, leads, consultations, revenue — and formats it into a clean narrative suitable for investor updates", "Claude + all data MCPs"],
      ].map((row, i) => new TableRow({
        children: row.map((cell, j) => rCell(cell, [2800,3313,2913][j], i % 2 === 0 ? C.white : C.light)),
      }))),
    ],
  }),
  new Paragraph({ spacing: { after: 200 }, children: [] }),

  // Summary box
  new Paragraph({
    spacing: { after: 80 },
    shading: { fill: "F0F4FF", type: ShadingType.CLEAR },
    children: [new TextRun({ text: "  Summary: Why Claude + MCP is the Right AI Infrastructure for Newmi", font: "Arial", size: 22, bold: true, color: C.dark })],
  }),
  para([run("Newmi does not need a single-channel ad tool — it needs a "), bold("unified AI growth layer"), run(" that can operate across all six functions above. Claude + MCP provides exactly this: one AI model connected to every tool in Newmi's stack, capable of executing from SEO schema generation to lead qualification to board reporting — all through natural language. As Newmi's digital infrastructure matures (SSR fixed, service pages live, GBP claimed), Claude + MCP scales with it without additional tooling investment.")]),
  pageBreak(),
];

// ════════════════════════════════════════════════════════════════════════════
//  BUILD DOCUMENT
// ════════════════════════════════════════════════════════════════════════════
const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } }, run: { font: "Arial", size: 20 } },
      }],
    }],
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 20, color: C.mid } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: C.dark },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: C.dark },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: C.mid },
        paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
      },
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            spacing: { after: 0 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.brand, space: 1 } },
            children: [
              new TextRun({ text: "NEWMI CARE  ", font: "Arial", size: 18, bold: true, color: C.brand }),
              new TextRun({ text: "Candidate Assignment — SEO + GEO Audit & AI Growth Operations", font: "Arial", size: 18, color: C.mid }),
            ],
          }),
        ],
      }),
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            spacing: { after: 0 },
            border: { top: { style: BorderStyle.SINGLE, size: 6, color: C.brand, space: 1 } },
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            children: [
              new TextRun({ text: "Confidential — June 2026", font: "Arial", size: 16, color: C.mid, italics: true }),
              new TextRun({ text: "\tPage ", font: "Arial", size: 16, color: C.mid }),
              new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: C.mid }),
            ],
          }),
        ],
      }),
    },
    children: [
      ...coverPage,
      ...tocPage,
      ...task1Header,
      ...executiveSummary,
      ...part1,
      ...part2,
      ...part3,
      ...part4,
      ...part5,
      ...part6,
      ...part7,
      ...part8,
      ...task2Header,
      ...task2Part1,
      ...task2Part2,
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("./Newmi_Care_Complete_Submission.docx", buffer);
  console.log("Done");
}).catch(err => {
  console.error(err);
  process.exit(1);
});