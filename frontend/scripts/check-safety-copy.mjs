#!/usr/bin/env node

import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const SRC_DIR = path.resolve("src");
const SCANNED_EXTENSIONS = new Set([".ts", ".tsx"]);

// These rules intentionally stay small and readable. They catch restricted
// medical/action wording when it appears outside negative or safety framing.
const RESTRICTED_PATTERNS = [
  {
    label: "diagnosis wording",
    pattern: /\bdiagnos(?:is|e|es|ed|ing|tic)\b/i,
  },
  {
    label: "treatment recommendation wording",
    pattern: /\btreatment\s+(?:advice|recommendation|plan|guidance)\b|\brecommend(?:s|ed|ing)?\s+(?:treatment|therapy|medication|cream|ointment)\b/i,
  },
  {
    label: "biopsy action wording",
    pattern: /\bbiops(?:y|ies|ied)\b/i,
  },
  {
    label: "referral action wording",
    pattern: /\breferr?al\b|\brefer(?:s|red|ring)?\b/i,
  },
  {
    label: "urgent review wording",
    pattern: /\burgent\s+(?:review|care|evaluation|assessment|attention)\b|\bseek\s+urgent\b/i,
  },
  {
    label: "clinical decision support wording",
    pattern: /\bclinical\s+decision\s+support\b|\bpatient[-\s]?care\s+directive\b/i,
  },
  {
    label: "patient-care directive language",
    pattern: /\b(?:start|stop|take|use|apply|prescribe|schedule|book|seek|go to|visit|consult)\s+(?:a\s+)?(?:doctor|dermatologist|clinician|medication|treatment|therapy|biopsy|appointment|urgent care|emergency|er)\b/i,
  },
  {
    label: "overclaiming certainty/validation/safety",
    pattern: /\b(?:clinically\s+validated|clinical\s+validation|validated\s+for\s+(?:clinical|patient)|clinical\s+certainty|certain\s+diagnosis|safe\s+for\s+patient|guaranteed|definitive|proven\s+safe|fully\s+validated)\b/i,
  },
];

// Documented exceptions for negative and safety-context copy. These are allowed
// because they reduce medical/action risk instead of asserting it.
const ALLOWLIST_CONTEXTS = [
  /\bnot\s+(?:a\s+)?diagnos(?:is|tic)\b/i,
  /\bdo\s+not\s+provide\s+diagnos(?:is|es|tic)\b/i,
  /\bnot\s+treatment\s+advice\b/i,
  /\bdo\s+not\s+provide\s+treatment\s+advice\b/i,
  /\bnot\s+clinical\s+decision\s+support\b/i,
  /\bnot\s+for\s+patient\s+care\b/i,
  /\beducational[-\s]?only\b/i,
  /\beducation\s+only\b/i,
  /\beducational\s+(?:review|context|discussion|model|mock|comparison|output|workflow)/i,
  /\bclinical\s+validation\b.*\b(?:not|no)\b|\b(?:not|no)\b.*\bclinical\s+validation\b/i,
  /\bmodel\s+confidence\s+is\s+not\s+clinical\s+certainty\b/i,
  /\bqualified\s+review\s+is\s+required\b/i,
  /\breal[-\s]?world\s+interpretation\s+requires\s+qualified\s+review\b/i,
  /\brequired\s+for\s+any\s+real\s+decision\b/i,
  /\bnot\s+a\s+substitute\s+for\s+qualified\s+review\b/i,
  /\brestricted[-_\s]?(?:term|terms|pattern|patterns|wording|copy)\b/i,
];

const REQUIRED_FRAMING = [
  {
    label: "educational-only or educational framing",
    pattern: /\beducational(?:[-\s]?only)?\b/i,
  },
  {
    label: "not diagnosis / not a diagnosis framing",
    pattern: /\bnot\s+(?:a\s+)?diagnosis\b/i,
  },
  {
    label: "not treatment advice framing",
    pattern: /\bnot\s+treatment\s+advice\b/i,
  },
  {
    label: "model confidence is not clinical certainty framing",
    pattern: /\bmodel\s+confidence\s+is\s+not\s+clinical\s+certainty\b|\bconfidence\b.{0,80}\bnot\b.{0,80}\bclinical\s+certainty\b/i,
  },
];

const failures = [];

const files = await findSourceFiles(SRC_DIR);
const aggregateSource = [];

for (const file of files) {
  const source = await readFile(file, "utf8");
  aggregateSource.push(source);
  checkFile(file, source);
}

const combinedSource = aggregateSource.join("\n");
for (const framing of REQUIRED_FRAMING) {
  if (!framing.pattern.test(combinedSource)) {
    failures.push({
      file: "frontend/src",
      line: "-",
      label: "missing required safety framing",
      snippet: framing.label,
    });
  }
}

if (failures.length > 0) {
  console.error("FAIL safety copy QA\n");
  for (const failure of failures) {
    console.error(`${failure.file}:${failure.line} - ${failure.label}`);
    console.error(`  ${failure.snippet}\n`);
  }
  process.exit(1);
}

console.log(`PASS safety copy QA (${files.length} frontend source files scanned)`);

async function findSourceFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const found = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      found.push(...await findSourceFiles(fullPath));
      continue;
    }

    if (entry.isFile() && SCANNED_EXTENSIONS.has(path.extname(entry.name))) {
      found.push(fullPath);
    }
  }

  return found.sort();
}

function checkFile(file, source) {
  const lines = source.split(/\r?\n/);
  lines.forEach((line, index) => {
    const context = [
      lines[index - 1] ?? "",
      line,
      lines[index + 1] ?? "",
    ].join(" ");

    for (const rule of RESTRICTED_PATTERNS) {
      if (!rule.pattern.test(line)) {
        continue;
      }

      if (isAllowedContext(context)) {
        continue;
      }

      failures.push({
        file: path.relative(process.cwd(), file),
        line: index + 1,
        label: rule.label,
        snippet: line.trim().replace(/\s+/g, " ").slice(0, 180),
      });
    }
  });
}

function isAllowedContext(context) {
  return ALLOWLIST_CONTEXTS.some((pattern) => pattern.test(context));
}
