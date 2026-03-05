import { execSync } from "child_process";
import fs from "fs";
import path from "path";

const OUTPUT_FILE = path.resolve("./docs/schema.sql");

const dump = execSync(
  "PGPASSWORD=postgres pg_dump --schema-only --no-acl --no-owner --schema=public --host=127.0.0.1 --port=54322 --username=postgres postgres",
  { encoding: "utf8", stdio: ["pipe", "pipe", "ignore"] },
);

// Collect CREATE TYPE ... AS ENUM blocks
const enums = [];

for (const match of dump.matchAll(
  /CREATE TYPE ([\w.]+) AS ENUM \(\n([\s\S]*?)\n\);/g,
)) {
  const values = match[2]
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .map((l) => l.replace(/,$/, ""));
  enums.push({ name: match[1], values });
}

// Collect CREATE TABLE blocks
const tables = new Map();
const tableOrder = [];

for (const match of dump.matchAll(
  /CREATE TABLE ([\w.]+) \(\n([\s\S]*?)\n\);/g,
)) {
  const name = match[1];
  const columns = match[2]
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .map((l) => l.replace(/,$/, ""));
  tableOrder.push(name);
  tables.set(name, { columns, constraints: [] });
}

// Collect ALTER TABLE ... ADD CONSTRAINT blocks and merge into tables
for (const match of dump.matchAll(
  /ALTER TABLE ONLY ([\w.]+)\n\s+ADD CONSTRAINT (\w+) (.+);/g,
)) {
  const table = tables.get(match[1]);
  if (table)
    table.constraints.push(`CONSTRAINT ${match[2]} ${match[3].trim()}`);
}

// Collect tables with RLS enabled
const rlsEnabled = new Set();
for (const match of dump.matchAll(
  /ALTER TABLE ([\w.]+) ENABLE ROW LEVEL SECURITY;/g,
)) {
  rlsEnabled.add(match[1]);
}

// Collect CREATE POLICY statements grouped by table
const policies = new Map();
for (const match of dump.matchAll(/CREATE POLICY [^;]+;/gs)) {
  const policyText = match[0].replace(/\s+/g, " ").trim();
  const tableMatch = policyText.match(/\bON ([\w.]+)/);
  if (tableMatch) {
    const table = tableMatch[1];
    if (!policies.has(table)) policies.set(table, []);
    policies.get(table).push(policyText);
  }
}

const lines = [
  "-- WARNING: This schema is for context only and is not meant to be run.",
  "-- Table order and constraints may not be valid for execution.",
  "",
];

for (const { name, values } of enums.sort((a, b) =>
  a.name.localeCompare(b.name),
)) {
  lines.push(`CREATE TYPE ${name} AS ENUM (`);
  values.forEach((v, i) =>
    lines.push(`  ${v}${i < values.length - 1 ? "," : ""}`),
  );
  lines.push(");");
  lines.push("");
}

for (const name of [...tableOrder].sort()) {
  const { columns, constraints } = tables.get(name);
  const all = [...columns, ...constraints];
  lines.push(`CREATE TABLE ${name} (`);
  all.forEach((line, i) =>
    lines.push(`  ${line}${i < all.length - 1 ? "," : ""}`),
  );
  lines.push(");");
  lines.push("");

  if (rlsEnabled.has(name)) {
    lines.push(`ALTER TABLE ${name} ENABLE ROW LEVEL SECURITY;`);
    lines.push("");
  }

  if (policies.has(name)) {
    for (const policy of policies.get(name)) {
      lines.push(policy);
    }
    lines.push("");
  }
}

fs.writeFileSync(OUTPUT_FILE, lines.join("\n"));
console.log(
  `✅ Schema written to docs/schema.sql (${tableOrder.length} tables)`,
);
