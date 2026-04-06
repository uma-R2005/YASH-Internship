import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import fs from "fs/promises";
import path from "path";
import { exec } from "child_process";
import { promisify } from "util";
import https from "https";
import http from "http";
import os from "os";
import crypto from "crypto";

const execAsync = promisify(exec);

const server = new McpServer({
  name: "my-mcp-server",
  version: "1.0.0",
});

function httpGet(url) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith("https") ? https : http;
    mod
      .get(url, { headers: { "User-Agent": "MCP-Server/1.0" } }, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve({ status: res.statusCode, body: data }));
      })
      .on("error", reject);
  });
}

// ─────────────────────────────────────────────
//  1. FILE SYSTEM TOOLS
// ─────────────────────────────────────────────

server.tool(
  "read_file",
  "Read the contents of a file",
  { path: z.string().describe("Absolute or relative file path") },
  async ({ path: filePath }) => {
    const content = await fs.readFile(filePath, "utf-8");
    return { content: [{ type: "text", text: content }] };
  }
);

server.tool(
  "write_file",
  "Write content to a file (creates or overwrites)",
  {
    path: z.string().describe("File path to write"),
    content: z.string().describe("Content to write"),
  },
  async ({ path: filePath, content }) => {
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, content, "utf-8");
    return { content: [{ type: "text", text: "Written to " + filePath }] };
  }
);

server.tool(
  "append_file",
  "Append text to the end of a file",
  { path: z.string(), content: z.string() },
  async ({ path: filePath, content }) => {
    await fs.appendFile(filePath, content, "utf-8");
    return { content: [{ type: "text", text: "Appended to " + filePath }] };
  }
);

server.tool(
  "delete_file",
  "Delete a file",
  { path: z.string() },
  async ({ path: filePath }) => {
    await fs.unlink(filePath);
    return { content: [{ type: "text", text: "Deleted " + filePath }] };
  }
);

server.tool(
  "list_directory",
  "List files and folders in a directory",
  {
    path: z.string().describe("Directory path"),
    recursive: z.boolean().optional().default(false),
  },
  async ({ path: dirPath, recursive }) => {
    async function walk(dir, depth = 0) {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      let result = [];
      for (const e of entries) {
        const indent = "  ".repeat(depth);
        const full = path.join(dir, e.name);
        if (e.isDirectory()) {
          result.push(indent + "[DIR] " + e.name + "/");
          if (recursive && depth < 3) result.push(...(await walk(full, depth + 1)));
        } else {
          const stat = await fs.stat(full);
          result.push(indent + "[FILE] " + e.name + " (" + (stat.size / 1024).toFixed(1) + " KB)");
        }
      }
      return result;
    }
    const lines = await walk(dirPath);
    return { content: [{ type: "text", text: lines.join("\n") }] };
  }
);

server.tool(
  "move_file",
  "Move or rename a file",
  { source: z.string(), destination: z.string() },
  async ({ source, destination }) => {
    await fs.rename(source, destination);
    return { content: [{ type: "text", text: "Moved " + source + " to " + destination }] };
  }
);

server.tool(
  "copy_file",
  "Copy a file to a new location",
  { source: z.string(), destination: z.string() },
  async ({ source, destination }) => {
    await fs.copyFile(source, destination);
    return { content: [{ type: "text", text: "Copied " + source + " to " + destination }] };
  }
);

server.tool(
  "get_file_info",
  "Get metadata about a file (size, dates, type)",
  { path: z.string() },
  async ({ path: filePath }) => {
    const stat = await fs.stat(filePath);
    const info = {
      path: filePath,
      size_bytes: stat.size,
      size_kb: (stat.size / 1024).toFixed(2),
      created: stat.birthtime.toISOString(),
      modified: stat.mtime.toISOString(),
      is_file: stat.isFile(),
      is_directory: stat.isDirectory(),
    };
    return { content: [{ type: "text", text: JSON.stringify(info, null, 2) }] };
  }
);

server.tool(
  "search_files",
  "Search for files by name pattern in a directory",
  {
    directory: z.string(),
    pattern: z.string().describe("Filename pattern to match e.g. *.js"),
  },
  async ({ directory, pattern }) => {
    const regex = new RegExp(pattern.replace("*", ".*"), "i");
    const results = [];
    async function walk(dir) {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      for (const e of entries) {
        const full = path.join(dir, e.name);
        if (e.isDirectory() && !e.name.startsWith(".") && e.name !== "node_modules") {
          await walk(full);
        } else if (regex.test(e.name)) {
          results.push(full);
        }
      }
    }
    await walk(directory);
    return {
      content: [{ type: "text", text: results.length ? results.join("\n") : "No files found" }],
    };
  }
);

server.tool(
  "grep_files",
  "Search for text content within files",
  {
    directory: z.string(),
    search_text: z.string(),
    file_extension: z.string().optional().default(""),
  },
  async ({ directory, search_text, file_extension }) => {
    const matches = [];
    async function walk(dir) {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      for (const e of entries) {
        const full = path.join(dir, e.name);
        if (e.isDirectory() && !e.name.startsWith(".") && e.name !== "node_modules") {
          await walk(full);
        } else if (!file_extension || e.name.endsWith(file_extension)) {
          try {
            const content = await fs.readFile(full, "utf-8");
            const lines = content.split("\n");
            lines.forEach((line, i) => {
              if (line.includes(search_text)) {
                matches.push(full + ":" + (i + 1) + ": " + line.trim());
              }
            });
          } catch {}
        }
      }
    }
    await walk(directory);
    const text = matches.length
      ? "Found " + matches.length + " matches:\n" + matches.slice(0, 50).join("\n")
      : "No matches found";
    return { content: [{ type: "text", text }] };
  }
);

// ─────────────────────────────────────────────
//  2. SHELL / CODE EXECUTION TOOLS
// ─────────────────────────────────────────────

server.tool(
  "run_command",
  "Run a shell command and return stdout/stderr",
  {
    command: z.string().describe("Shell command to execute"),
    cwd: z.string().optional().describe("Working directory"),
    timeout_ms: z.number().optional().default(15000),
  },
  async ({ command, cwd, timeout_ms }) => {
    const { stdout, stderr } = await execAsync(command, {
      cwd: cwd || process.cwd(),
      timeout: timeout_ms,
    });
    return {
      content: [{
        type: "text",
        text: "STDOUT:\n" + (stdout || "(empty)") + "\n\nSTDERR:\n" + (stderr || "(none)"),
      }],
    };
  }
);

server.tool(
  "run_python_code",
  "Execute a Python script (requires Python installed)",
  {
    code: z.string().describe("Python code to run"),
    args: z.array(z.string()).optional().default([]),
  },
  async ({ code, args }) => {
    const tmpFile = path.join(os.tmpdir(), "mcp_py_" + Date.now() + ".py");
    await fs.writeFile(tmpFile, code, "utf-8");
    const { stdout, stderr } = await execAsync(
      "python3 " + tmpFile + " " + args.join(" "),
      { timeout: 15000 }
    );
    await fs.unlink(tmpFile).catch(() => {});
    return { content: [{ type: "text", text: stdout || stderr || "(no output)" }] };
  }
);

server.tool(
  "run_node_code",
  "Execute a Node.js script",
  { code: z.string().describe("JavaScript (Node.js) code to run") },
  async ({ code }) => {
    const tmpFile = path.join(os.tmpdir(), "mcp_js_" + Date.now() + ".mjs");
    await fs.writeFile(tmpFile, code, "utf-8");
    const { stdout, stderr } = await execAsync("node " + tmpFile, { timeout: 15000 });
    await fs.unlink(tmpFile).catch(() => {});
    return { content: [{ type: "text", text: stdout || stderr || "(no output)" }] };
  }
);

server.tool(
  "get_env_variable",
  "Get the value of an environment variable",
  { name: z.string() },
  async ({ name }) => {
    const value = process.env[name];
    return {
      content: [{
        type: "text",
        text: value !== undefined ? name + "=" + value : name + " is not set",
      }],
    };
  }
);

// ─────────────────────────────────────────────
//  3. WEB / HTTP TOOLS
// ─────────────────────────────────────────────

server.tool(
  "fetch_url",
  "Fetch raw content from a URL",
  {
    url: z.string().url(),
    max_chars: z.number().optional().default(5000),
  },
  async ({ url, max_chars }) => {
    const { status, body } = await httpGet(url);
    return { content: [{ type: "text", text: "Status: " + status + "\n\n" + body.slice(0, max_chars) }] };
  }
);

server.tool(
  "check_url_status",
  "Check if a URL is reachable and get its HTTP status code",
  { url: z.string().url() },
  async ({ url }) => {
    const { status } = await httpGet(url);
    const ok = status >= 200 && status < 400;
    return {
      content: [{ type: "text", text: url + " => HTTP " + status + " (" + (ok ? "OK" : "Error") + ")" }],
    };
  }
);

server.tool(
  "search_wikipedia",
  "Search Wikipedia and return a summary (free, no API key needed)",
  { query: z.string() },
  async ({ query }) => {
    const { body } = await httpGet("https://en.wikipedia.org/api/rest_v1/page/summary/" + encodeURIComponent(query));
    const data = JSON.parse(body);
    if (data.extract) {
      return {
        content: [{
          type: "text",
          text: data.title + "\n\n" + data.extract + "\n\nSource: " + (data.content_urls?.desktop?.page || "Wikipedia"),
        }],
      };
    }
    return { content: [{ type: "text", text: "No Wikipedia article found for: " + query }] };
  }
);

server.tool(
  "get_public_ip",
  "Get your current public IP address",
  {},
  async () => {
    const { body } = await httpGet("https://api.ipify.org?format=json");
    const { ip } = JSON.parse(body);
    return { content: [{ type: "text", text: "Public IP: " + ip }] };
  }
);

server.tool(
  "get_exchange_rates",
  "Get live currency exchange rates (free, no API key needed)",
  { base_currency: z.string().default("USD").describe("Base currency code e.g. USD, EUR, INR") },
  async ({ base_currency }) => {
    const { body } = await httpGet("https://open.er-api.com/v6/latest/" + base_currency.toUpperCase());
    const data = JSON.parse(body);
    if (data.result === "success") {
      const top = ["USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD", "CNY", "SGD", "AED"];
      const rates = top
        .filter(c => c !== base_currency.toUpperCase())
        .map(c => c + ": " + data.rates[c])
        .join("\n");
      return { content: [{ type: "text", text: "Exchange rates (base: " + base_currency.toUpperCase() + "):\n\n" + rates }] };
    }
    return { content: [{ type: "text", text: "Could not fetch exchange rates" }] };
  }
);

server.tool(
  "get_weather",
  "Get current weather for a city (free Open-Meteo, no API key needed)",
  {
    city: z.string().describe("City name"),
    country_code: z.string().optional().default("IN"),
  },
  async ({ city, country_code }) => {
    const { body: geoBody } = await httpGet(
      "https://geocoding-api.open-meteo.com/v1/search?name=" + encodeURIComponent(city) + "&count=1&country=" + country_code
    );
    const geo = JSON.parse(geoBody);
    if (!geo.results?.length) return { content: [{ type: "text", text: "City not found: " + city }] };
    const { latitude, longitude, name, country } = geo.results[0];
    const { body: wxBody } = await httpGet(
      "https://api.open-meteo.com/v1/forecast?latitude=" + latitude + "&longitude=" + longitude + "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&timezone=auto"
    );
    const wx = JSON.parse(wxBody);
    const c = wx.current;
    const codes = { 0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Foggy", 61: "Light rain", 63: "Moderate rain", 80: "Rain showers", 95: "Thunderstorm" };
    return {
      content: [{
        type: "text",
        text: "Weather in " + name + ", " + country + ":\nTemperature: " + c.temperature_2m + "C\nHumidity: " + c.relative_humidity_2m + "%\nWind: " + c.wind_speed_10m + " km/h\nCondition: " + (codes[c.weather_code] || "Code " + c.weather_code),
      }],
    };
  }
);

server.tool(
  "get_joke",
  "Get a random programming or general joke (free)",
  { category: z.enum(["programming", "general", "dad"]).optional().default("programming") },
  async ({ category }) => {
    if (category === "dad") {
      const { body } = await httpGet("https://icanhazdadjoke.com/?format=json");
      return { content: [{ type: "text", text: JSON.parse(body).joke }] };
    }
    const { body } = await httpGet("https://official-joke-api.appspot.com/jokes/" + category + "/random");
    const [{ setup, punchline }] = JSON.parse(body);
    return { content: [{ type: "text", text: setup + "\n\n..." + punchline }] };
  }
);

// ─────────────────────────────────────────────
//  4. SYSTEM INFO TOOLS
// ─────────────────────────────────────────────

server.tool(
  "get_system_info",
  "Get information about the current system (OS, CPU, RAM, etc.)",
  {},
  async () => {
    const info = {
      platform: os.platform(),
      arch: os.arch(),
      os_release: os.release(),
      hostname: os.hostname(),
      cpu_count: os.cpus().length,
      cpu_model: os.cpus()[0]?.model,
      total_ram_gb: (os.totalmem() / 1024 ** 3).toFixed(2),
      free_ram_gb: (os.freemem() / 1024 ** 3).toFixed(2),
      uptime_hours: (os.uptime() / 3600).toFixed(1),
      home_dir: os.homedir(),
      node_version: process.version,
    };
    return { content: [{ type: "text", text: JSON.stringify(info, null, 2) }] };
  }
);

server.tool(
  "get_current_time",
  "Get the current date and time in any timezone",
  { timezone: z.string().optional().default("Asia/Kolkata") },
  async ({ timezone }) => {
    const now = new Date();
    const formatted = new Intl.DateTimeFormat("en-US", { timeZone: timezone, dateStyle: "full", timeStyle: "long" }).format(now);
    return {
      content: [{
        type: "text",
        text: "Time in " + timezone + ":\n" + formatted + "\n\nISO: " + now.toISOString() + "\nUnix: " + Math.floor(now.getTime() / 1000),
      }],
    };
  }
);

server.tool(
  "list_running_processes",
  "List currently running processes",
  {},
  async () => {
    const cmd = os.platform() === "win32" ? "tasklist" : "ps aux --sort=-%mem | head -20";
    const { stdout } = await execAsync(cmd, { timeout: 5000 });
    return { content: [{ type: "text", text: stdout }] };
  }
);

server.tool(
  "get_disk_usage",
  "Get disk usage information",
  {},
  async () => {
    const cmd = os.platform() === "win32" ? "wmic logicaldisk get size,freespace,caption" : "df -h";
    const { stdout } = await execAsync(cmd, { timeout: 5000 });
    return { content: [{ type: "text", text: stdout }] };
  }
);

// ─────────────────────────────────────────────
//  5. TEXT / UTILITY TOOLS
// ─────────────────────────────────────────────

server.tool(
  "generate_uuid",
  "Generate one or more UUIDs",
  { count: z.number().min(1).max(20).optional().default(1) },
  async ({ count }) => {
    const ids = Array.from({ length: count }, () => crypto.randomUUID());
    return { content: [{ type: "text", text: ids.join("\n") }] };
  }
);

server.tool(
  "hash_text",
  "Hash a string using MD5, SHA1, or SHA256",
  {
    text: z.string(),
    algorithm: z.enum(["md5", "sha1", "sha256"]).optional().default("sha256"),
  },
  async ({ text, algorithm }) => {
    const hash = crypto.createHash(algorithm).update(text).digest("hex");
    return { content: [{ type: "text", text: algorithm.toUpperCase() + ": " + hash }] };
  }
);

server.tool(
  "encode_decode_base64",
  "Encode or decode a string in Base64",
  {
    text: z.string(),
    mode: z.enum(["encode", "decode"]).default("encode"),
  },
  async ({ text, mode }) => {
    const result = mode === "encode"
      ? Buffer.from(text, "utf-8").toString("base64")
      : Buffer.from(text, "base64").toString("utf-8");
    return { content: [{ type: "text", text: result }] };
  }
);

server.tool(
  "count_words",
  "Count words, lines, and characters in a text",
  { text: z.string() },
  async ({ text }) => {
    const words = text.trim().split(/\s+/).filter(Boolean).length;
    const lines = text.split("\n").length;
    const chars = text.length;
    const sentences = text.split(/[.!?]+/).filter(Boolean).length;
    return {
      content: [{
        type: "text",
        text: "Characters: " + chars + "\nWords: " + words + "\nLines: " + lines + "\nSentences: " + sentences,
      }],
    };
  }
);

server.tool(
  "format_json",
  "Format / pretty-print a JSON string",
  { json: z.string(), indent: z.number().optional().default(2) },
  async ({ json, indent }) => {
    const parsed = JSON.parse(json);
    return { content: [{ type: "text", text: JSON.stringify(parsed, null, indent) }] };
  }
);

server.tool(
  "generate_random_password",
  "Generate a secure random password",
  {
    length: z.number().min(8).max(128).optional().default(16),
    include_symbols: z.boolean().optional().default(true),
  },
  async ({ length, include_symbols }) => {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" + (include_symbols ? "!@#$%^&*()-_=+[]{}|;:,.<>?" : "");
    const password = Array.from({ length }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
    return { content: [{ type: "text", text: password }] };
  }
);

server.tool(
  "calculate",
  "Evaluate a mathematical expression",
  { expression: z.string() },
  async ({ expression }) => {
    const safe = expression.replace(/[^0-9+\-*/().,\s%]/g, "");
    if (!safe.trim()) return { content: [{ type: "text", text: "Invalid expression" }] };
    const result = Function('"use strict"; return (' + safe + ')')();
    return { content: [{ type: "text", text: expression + " = " + result }] };
  }
);

server.tool(
  "convert_units",
  "Convert between common units (length, weight, temperature, data)",
  {
    value: z.number(),
    from_unit: z.string(),
    to_unit: z.string(),
  },
  async ({ value, from_unit, to_unit }) => {
    const from = from_unit.toLowerCase();
    const to = to_unit.toLowerCase();
    const conversions = {
      "km-miles": v => v * 0.621371, "miles-km": v => v * 1.60934,
      "m-ft": v => v * 3.28084, "ft-m": v => v / 3.28084,
      "cm-inches": v => v / 2.54, "inches-cm": v => v * 2.54,
      "kg-lb": v => v * 2.20462, "lb-kg": v => v / 2.20462,
      "c-f": v => (v * 9) / 5 + 32, "f-c": v => ((v - 32) * 5) / 9,
      "c-k": v => v + 273.15, "k-c": v => v - 273.15,
      "mb-gb": v => v / 1024, "gb-mb": v => v * 1024,
      "gb-tb": v => v / 1024, "tb-gb": v => v * 1024,
      "kb-mb": v => v / 1024, "mb-kb": v => v * 1024,
    };
    const fn = conversions[from + "-" + to];
    if (!fn) return { content: [{ type: "text", text: "Conversion not supported: " + from + " to " + to }] };
    return { content: [{ type: "text", text: value + " " + from_unit + " = " + fn(value).toFixed(4) + " " + to_unit }] };
  }
);

// ─────────────────────────────────────────────
//  6. GIT TOOLS
// ─────────────────────────────────────────────

server.tool(
  "git_status",
  "Get git status for a repository",
  { repo_path: z.string() },
  async ({ repo_path }) => {
    const { stdout } = await execAsync("git status", { cwd: repo_path, timeout: 5000 });
    return { content: [{ type: "text", text: stdout }] };
  }
);

server.tool(
  "git_log",
  "Get recent git commits",
  { repo_path: z.string(), count: z.number().optional().default(10) },
  async ({ repo_path, count }) => {
    const { stdout } = await execAsync("git log --oneline --graph -" + count, { cwd: repo_path, timeout: 5000 });
    return { content: [{ type: "text", text: stdout }] };
  }
);

server.tool(
  "git_diff",
  "Get the current uncommitted changes",
  { repo_path: z.string() },
  async ({ repo_path }) => {
    const { stdout } = await execAsync("git diff", { cwd: repo_path, timeout: 5000 });
    return { content: [{ type: "text", text: stdout || "No changes (working tree clean)" }] };
  }
);

server.tool(
  "git_commit",
  "Stage all changes and create a git commit",
  { repo_path: z.string(), message: z.string() },
  async ({ repo_path, message }) => {
    await execAsync("git add -A", { cwd: repo_path });
    const { stdout } = await execAsync('git commit -m "' + message + '"', { cwd: repo_path });
    return { content: [{ type: "text", text: stdout }] };
  }
);

// ─────────────────────────────────────────────
//  7. NOTES / MEMORY
// ─────────────────────────────────────────────

const NOTES_FILE = path.join(os.homedir(), ".mcp_notes.json");
async function loadNotes() {
  try { return JSON.parse(await fs.readFile(NOTES_FILE, "utf-8")); } catch { return {}; }
}
async function saveNotes(notes) {
  await fs.writeFile(NOTES_FILE, JSON.stringify(notes, null, 2), "utf-8");
}

server.tool("save_note", "Save a named note", { key: z.string(), content: z.string() }, async ({ key, content }) => {
  const notes = await loadNotes();
  notes[key] = { content, updated: new Date().toISOString() };
  await saveNotes(notes);
  return { content: [{ type: "text", text: "Note saved: " + key }] };
});

server.tool("get_note", "Retrieve a saved note", { key: z.string() }, async ({ key }) => {
  const notes = await loadNotes();
  const note = notes[key];
  if (!note) return { content: [{ type: "text", text: "No note found: " + key }] };
  return { content: [{ type: "text", text: "[" + note.updated + "]\n\n" + note.content }] };
});

server.tool("list_notes", "List all saved notes", {}, async () => {
  const notes = await loadNotes();
  const keys = Object.keys(notes);
  return { content: [{ type: "text", text: keys.length ? keys.map(k => "- " + k + " (" + notes[k].updated + ")").join("\n") : "No notes saved yet." }] };
});

server.tool("delete_note", "Delete a saved note", { key: z.string() }, async ({ key }) => {
  const notes = await loadNotes();
  if (!notes[key]) return { content: [{ type: "text", text: "Note not found: " + key }] };
  delete notes[key];
  await saveNotes(notes);
  return { content: [{ type: "text", text: "Note deleted: " + key }] };
});

// ─────────────────────────────────────────────
//  8. MUSIC & LYRICS
// ─────────────────────────────────────────────

server.tool(
  "search_music",
  "Search for a song and get info like artist, album, genre (free)",
  { query: z.string() },
  async ({ query }) => {
    const { body } = await httpGet("https://itunes.apple.com/search?term=" + encodeURIComponent(query) + "&media=music&limit=5");
    const data = JSON.parse(body);
    if (!data.results?.length) return { content: [{ type: "text", text: "No results for: " + query }] };
    const results = data.results.map((t, i) =>
      (i + 1) + ". " + (t.trackName || "Unknown") + "\n   Artist: " + t.artistName + "\n   Album: " + (t.collectionName || "Single") + "\n   Genre: " + (t.primaryGenreName || "Unknown") + "\n   Year: " + (t.releaseDate ? new Date(t.releaseDate).getFullYear() : "Unknown")
    ).join("\n\n");
    return { content: [{ type: "text", text: "Music results for: " + query + "\n\n" + results }] };
  }
);

server.tool(
  "get_lyrics",
  "Get lyrics for a song (free)",
  { artist: z.string(), song: z.string() },
  async ({ artist, song }) => {
    const url = "https://api.lyrics.ovh/v1/" + encodeURIComponent(artist) + "/" + encodeURIComponent(song);
    try {
      const { status, body } = await httpGet(url);
      if (status !== 200) return { content: [{ type: "text", text: "Lyrics not found for: " + song + " by " + artist }] };
      const data = JSON.parse(body);
      if (!data.lyrics) return { content: [{ type: "text", text: "No lyrics available for: " + song }] };
      const lyrics = data.lyrics.length > 3000 ? data.lyrics.slice(0, 3000) + "\n\n... (truncated)" : data.lyrics;
      return { content: [{ type: "text", text: song + " by " + artist + "\n\n" + lyrics }] };
    } catch {
      return { content: [{ type: "text", text: "Could not fetch lyrics for: " + song }] };
    }
  }
);

server.tool(
  "get_top_charts",
  "Get current top music charts by genre (free iTunes)",
  {
    genre: z.enum(["pop", "rock", "hip-hop", "electronic", "classical", "country", "all"]).optional().default("all"),
    limit: z.number().min(1).max(20).optional().default(10),
  },
  async ({ genre, limit }) => {
    const genreIds = { pop: 14, rock: 21, "hip-hop": 18, electronic: 7, classical: 5, country: 6, all: 0 };
    const genreId = genreIds[genre] || 0;
    const url = "https://itunes.apple.com/us/rss/topsongs/limit=" + limit + (genreId ? "/genre=" + genreId : "") + "/json";
    const { body } = await httpGet(url);
    const entries = JSON.parse(body)?.feed?.entry;
    if (!entries?.length) return { content: [{ type: "text", text: "Could not fetch charts right now" }] };
    const chart = entries.map((e, i) => (i + 1) + ". " + e["im:name"]?.label + " -- " + e["im:artist"]?.label).join("\n");
    return { content: [{ type: "text", text: "Top " + limit + " " + (genre === "all" ? "" : genre + " ") + "songs (iTunes):\n\n" + chart }] };
  }
);

// ─────────────────────────────────────────────
//  9. QR CODE GENERATOR
// ─────────────────────────────────────────────

server.tool(
  "generate_qr_code",
  "Generate a QR code and save as SVG file",
  {
    text: z.string().describe("Text or URL to encode"),
    output_path: z.string().describe("File path to save e.g. C:\\Users\\R Uma\\Desktop\\qr.svg"),
    size: z.number().min(100).max(1000).optional().default(300),
  },
  async ({ text, output_path, size }) => {
    const apiUrl = "https://api.qrserver.com/v1/create-qr-code/?size=" + size + "x" + size + "&data=" + encodeURIComponent(text) + "&format=svg";
    const { body } = await httpGet(apiUrl);
    if (!body.includes("<svg")) return { content: [{ type: "text", text: "Failed to generate QR code" }] };
    await fs.mkdir(path.dirname(output_path), { recursive: true });
    await fs.writeFile(output_path, body, "utf-8");
    return { content: [{ type: "text", text: "QR Code saved!\nFile: " + output_path + "\nEncoded: " + text + "\nOpen in any browser to view." }] };
  }
);

server.tool(
  "generate_qr_url",
  "Get a direct URL link to a QR code image",
  { text: z.string(), size: z.number().min(100).max(1000).optional().default(300) },
  async ({ text, size }) => {
    const url = "https://api.qrserver.com/v1/create-qr-code/?size=" + size + "x" + size + "&data=" + encodeURIComponent(text);
    return { content: [{ type: "text", text: "QR Code URL:\n" + url + "\n\nOpen in browser to view/download.\nEncoded: " + text }] };
  }
);

// ─────────────────────────────────────────────
//  10. EMAIL SENDER (Gmail SMTP)
// ─────────────────────────────────────────────

server.tool(
  "send_email",
  "Send an email via Gmail SMTP using an App Password (free)",
  {
    to: z.string(),
    subject: z.string(),
    body: z.string(),
    from_email: z.string(),
    app_password: z.string().describe("Gmail App Password from myaccount.google.com/apppasswords"),
  },
  async ({ to, subject, body, from_email, app_password }) => {
    const script = `
import nodemailer from 'nodemailer';
const t = nodemailer.createTransport({
  host: 'smtp.gmail.com', port: 587, secure: false,
  auth: { user: ${JSON.stringify(from_email)}, pass: ${JSON.stringify(app_password)} },
});
try {
  const info = await t.sendMail({ from: ${JSON.stringify(from_email)}, to: ${JSON.stringify(to)}, subject: ${JSON.stringify(subject)}, text: ${JSON.stringify(body)} });
  console.log('SUCCESS:' + info.messageId);
} catch(e) { console.error('ERROR:' + e.message); }
`;
    const tmpFile = path.join(os.tmpdir(), "mcp_mail_" + Date.now() + ".mjs");
    await fs.writeFile(tmpFile, script, "utf-8");
    try {
      const projectPath = "C:\\Users\\R Uma\\mcp-server";
      const { stdout, stderr } = await execAsync("node " + tmpFile, { timeout: 15000, cwd: projectPath });
      await fs.unlink(tmpFile).catch(() => {});
      if (stdout.includes("SUCCESS:")) {
        return { content: [{ type: "text", text: "Email sent!\nTo: " + to + "\nSubject: " + subject }] };
      }
      return { content: [{ type: "text", text: "Failed: " + (stderr || stdout) }] };
    } catch (err) {
      await fs.unlink(tmpFile).catch(() => {});
      return { content: [{ type: "text", text: "Error: " + err.message }] };
    }
  }
);

server.tool(
  "setup_email_guide",
  "Get step-by-step Gmail App Password setup instructions",
  {},
  async () => ({
    content: [{
      type: "text",
      text: "Gmail App Password Setup\n\n1. Go to myaccount.google.com/security\n2. Enable 2-Step Verification\n3. Go to myaccount.google.com/apppasswords\n4. Select app: Mail, device: Windows Computer\n5. Click Generate\n6. Copy the 16-character password (remove spaces)\n7. Use it as app_password in send_email tool\n\nAlso run: npm install nodemailer",
    }],
  })
);

// ─────────────────────────────────────────────
//  11. SECOND BRAIN
// ─────────────────────────────────────────────

const BRAIN_FILE = path.join(os.homedir(), ".mcp_second_brain.json");
async function loadBrain() {
  try { return JSON.parse(await fs.readFile(BRAIN_FILE, "utf-8")); } catch { return { memories: [], topics: {} }; }
}
async function saveBrain(brain) {
  await fs.writeFile(BRAIN_FILE, JSON.stringify(brain, null, 2), "utf-8");
}

server.tool(
  "brain_remember",
  "Save an idea or fact to your Second Brain with auto-tagging and auto-connection to related ideas",
  {
    content: z.string().describe("The idea, fact, or note to remember"),
    topic: z.string().optional().describe("Topic e.g. coding, life, work, ideas"),
  },
  async ({ content, topic }) => {
    const brain = await loadBrain();
    const stopWords = new Set(["the", "a", "an", "is", "in", "on", "at", "to", "for", "of", "and", "or", "but", "it", "this", "that", "with", "was", "are", "be"]);
    const autoTags = [...new Set(content.toLowerCase().split(/\s+/).filter(w => w.length > 4 && !stopWords.has(w)))].slice(0, 5);
    const memory = {
      id: crypto.randomUUID(),
      content,
      topic: topic || "general",
      tags: autoTags,
      created: new Date().toISOString(),
      connections: [],
    };
    const related = brain.memories.filter(m => m.tags.some(t => autoTags.includes(t)) || m.topic === memory.topic);
    if (related.length > 0) {
      memory.connections = related.slice(0, 3).map(r => r.id);
      related.slice(0, 3).forEach(r => {
        if (!r.connections) r.connections = [];
        if (!r.connections.includes(memory.id)) r.connections.push(memory.id);
      });
    }
    brain.memories.push(memory);
    if (!brain.topics[memory.topic]) brain.topics[memory.topic] = [];
    brain.topics[memory.topic].push(memory.id);
    await saveBrain(brain);
    const connMsg = related.length > 0
      ? "\nAuto-connected to " + related.length + " related idea(s):\n" + related.slice(0, 3).map(r => "  - " + r.content.slice(0, 60) + "...").join("\n")
      : "\nFirst memory on this topic.";
    return {
      content: [{
        type: "text",
        text: "Saved to Second Brain!\nID: " + memory.id.slice(0, 8) + "\nTopic: " + memory.topic + "\nTags: " + autoTags.join(", ") + connMsg + "\n\nTotal memories: " + brain.memories.length,
      }],
    };
  }
);

server.tool(
  "brain_search",
  "Search your Second Brain by keyword or topic",
  {
    query: z.string(),
    topic: z.string().optional(),
    limit: z.number().optional().default(5),
  },
  async ({ query, topic, limit }) => {
    const brain = await loadBrain();
    if (!brain.memories.length) return { content: [{ type: "text", text: "Second Brain is empty. Use brain_remember to add ideas!" }] };
    const q = query.toLowerCase();
    let results = brain.memories.filter(m =>
      (m.content.toLowerCase().includes(q) || m.tags.some(t => t.includes(q)) || m.topic.toLowerCase().includes(q)) &&
      (!topic || m.topic === topic)
    ).slice(0, limit);
    if (!results.length) return { content: [{ type: "text", text: "No memories found for: " + query }] };
    const output = results.map((m, i) =>
      (i + 1) + ". [" + m.topic + "] " + m.content + "\n   Tags: " + m.tags.join(", ") + "\n   Saved: " + new Date(m.created).toLocaleDateString() + (m.connections?.length ? "\n   Connected to " + m.connections.length + " idea(s)" : "")
    ).join("\n\n");
    return { content: [{ type: "text", text: "Found " + results.length + " memories for: " + query + "\n\n" + output }] };
  }
);

server.tool(
  "brain_connections",
  "Show all ideas connected to a specific memory",
  { memory_id_or_keyword: z.string() },
  async ({ memory_id_or_keyword }) => {
    const brain = await loadBrain();
    const mem = brain.memories.find(m =>
      m.id.startsWith(memory_id_or_keyword) || m.content.toLowerCase().includes(memory_id_or_keyword.toLowerCase())
    );
    if (!mem) return { content: [{ type: "text", text: "No memory found for: " + memory_id_or_keyword }] };
    const connected = brain.memories.filter(m => mem.connections?.includes(m.id));
    const output = connected.length
      ? connected.map((m, i) => (i + 1) + ". [" + m.topic + "] " + m.content + "\n   Tags: " + m.tags.join(", ")).join("\n\n")
      : "No connections yet.";
    return {
      content: [{
        type: "text",
        text: "Memory: " + mem.content + "\nTopic: " + mem.topic + " | Tags: " + mem.tags.join(", ") + "\n\nConnected Ideas (" + connected.length + "):\n\n" + output,
      }],
    };
  }
);

server.tool(
  "brain_map",
  "Show your full knowledge map - all topics, counts, and most connected ideas",
  {},
  async () => {
    const brain = await loadBrain();
    if (!brain.memories.length) return { content: [{ type: "text", text: "Second Brain is empty. Start with brain_remember!" }] };
    const topicSummary = Object.entries(brain.topics).map(([t, ids]) => "  " + t + ": " + ids.length + " memories").join("\n");
    const totalConns = brain.memories.reduce((s, m) => s + (m.connections?.length || 0), 0);
    const mostConnected = [...brain.memories]
      .sort((a, b) => (b.connections?.length || 0) - (a.connections?.length || 0))
      .slice(0, 3)
      .map(m => "  - " + m.content.slice(0, 50) + "... (" + (m.connections?.length || 0) + " connections)");
    const recent = [...brain.memories]
      .sort((a, b) => new Date(b.created) - new Date(a.created))
      .slice(0, 3)
      .map(m => "  - [" + m.topic + "] " + m.content.slice(0, 60) + "...");
    return {
      content: [{
        type: "text",
        text: "YOUR SECOND BRAIN MAP\n" + "=".repeat(35) + "\n\nTotal memories: " + brain.memories.length + "\nTotal connections: " + totalConns + "\nTopics: " + Object.keys(brain.topics).length + "\n\nBy Topic:\n" + topicSummary + "\n\nMost Connected:\n" + (mostConnected.join("\n") || "  None yet") + "\n\nRecently Added:\n" + recent.join("\n"),
      }],
    };
  }
);

server.tool(
  "brain_forget",
  "Delete a memory from your Second Brain",
  { memory_id_or_keyword: z.string() },
  async ({ memory_id_or_keyword }) => {
    const brain = await loadBrain();
    const idx = brain.memories.findIndex(m =>
      m.id.startsWith(memory_id_or_keyword) || m.content.toLowerCase().includes(memory_id_or_keyword.toLowerCase())
    );
    if (idx === -1) return { content: [{ type: "text", text: "No memory found for: " + memory_id_or_keyword }] };
    const removed = brain.memories.splice(idx, 1)[0];
    if (brain.topics[removed.topic]) brain.topics[removed.topic] = brain.topics[removed.topic].filter(id => id !== removed.id);
    await saveBrain(brain);
    return { content: [{ type: "text", text: "Forgotten: " + removed.content.slice(0, 80) + "\nRemaining: " + brain.memories.length + " memories" }] };
  }
);

// ─────────────────────────────────────────────
//  12. SCREENSHOT — ROBUST MULTI-METHOD
// ─────────────────────────────────────────────

// Groq Vision — defined FIRST so all tools below can use it
function groqVision(base64Image, prompt, apiKey) {
  return new Promise((resolve) => {
    const body = JSON.stringify({
      model: "meta-llama/llama-4-scout-17b-16e-instruct",
      messages: [{
        role: "user",
        content: [
          { type: "text", text: prompt },
          { type: "image_url", image_url: { url: "data:image/png;base64," + base64Image } },
        ],
      }],
      max_tokens: 1024,
    });
    const options = {
      hostname: "api.groq.com",
      path: "/openai/v1/chat/completions",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + apiKey,
        "Content-Length": Buffer.byteLength(body),
      },
    };
    const req = https.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          const parsed = JSON.parse(data);
          const text = parsed?.choices?.[0]?.message?.content;
          resolve(text || "No response from Groq: " + data.slice(0, 300));
        } catch { resolve("Parse error: " + data.slice(0, 200)); }
      });
    });
    req.on("error", (e) => resolve("Network error: " + e.message));
    req.write(body);
    req.end();
  });
}

function psEncoded(psScript) {
  const encoded = Buffer.from(psScript, "utf16le").toString("base64");
  return `powershell -ExecutionPolicy Bypass -NonInteractive -WindowStyle Hidden -EncodedCommand ${encoded}`;
}

function buildScreenshotScript(savePath) {
  const safe = savePath.replace(/\\/g, "\\\\");
  return `
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
try {
  $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size, [System.Drawing.CopyPixelOperation]::SourceCopy)
  $bmp.Save("${safe}", [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose()
  Write-Output "OK"
} catch {
  Write-Error $_.Exception.Message
  exit 1
}
`.trim();
}

function buildBitBltScript(savePath) {
  const safe = savePath.replace(/\\/g, "\\\\");
  return `
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public class ScreenCapture {
    [DllImport("user32.dll")] public static extern IntPtr GetDesktopWindow();
    [DllImport("user32.dll")] public static extern IntPtr GetWindowDC(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
    [DllImport("gdi32.dll")] public static extern bool BitBlt(IntPtr hdc, int nXDest, int nYDest, int nWidth, int nHeight, IntPtr hdcSrc, int nXSrc, int nYSrc, uint dwRop);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    public static Bitmap Capture() {
        IntPtr desktop = GetDesktopWindow();
        RECT rect;
        GetWindowRect(desktop, out rect);
        int w = rect.Right - rect.Left;
        int h = rect.Bottom - rect.Top;
        IntPtr dc = GetWindowDC(desktop);
        Bitmap bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        Graphics g = Graphics.FromImage(bmp);
        IntPtr gdc = g.GetHdc();
        BitBlt(gdc, 0, 0, w, h, dc, 0, 0, 0x00CC0020);
        g.ReleaseHdc(gdc);
        g.Dispose();
        ReleaseDC(desktop, dc);
        return bmp;
    }
}
"@
try {
  $bmp = [ScreenCapture]::Capture()
  $bmp.Save("${safe}", [System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose()
  Write-Output "OK"
} catch {
  Write-Error $_.Exception.Message
  exit 1
}
`.trim();
}

function buildSmallScreenshotScript(savePath) {
  const safe = savePath.replace(/\\/g, "\\\\");
  return `
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
try {
  $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bmp = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size, [System.Drawing.CopyPixelOperation]::SourceCopy)
  $g.Dispose()
  $w = [int]($bounds.Width / 2)
  $h = [int]($bounds.Height / 2)
  $small = New-Object System.Drawing.Bitmap($bmp, (New-Object System.Drawing.Size($w, $h)))
  $small.Save("${safe}", [System.Drawing.Imaging.ImageFormat]::Png)
  $bmp.Dispose(); $small.Dispose()
  Write-Output "OK"
} catch {
  Write-Error $_.Exception.Message
  exit 1
}
`.trim();
}

async function takeScreenshot(savePath) {
  try {
    const { stdout, stderr } = await execAsync(psEncoded(buildScreenshotScript(savePath)), { timeout: 20000 });
    if (stdout.includes("OK")) {
      await fs.access(savePath);
      return { success: true, method: "CopyFromScreen" };
    }
    throw new Error(stderr || "No OK response");
  } catch (e1) {
    try {
      const { stdout: stdout2 } = await execAsync(psEncoded(buildBitBltScript(savePath)), { timeout: 20000 });
      if (stdout2.includes("OK")) {
        await fs.access(savePath);
        return { success: true, method: "BitBlt" };
      }
      throw new Error("BitBlt no OK response");
    } catch (e2) {
      return {
        success: false,
        error: `Method 1 (CopyFromScreen): ${e1.message}\nMethod 2 (BitBlt): ${e2.message}`,
      };
    }
  }
}

server.tool(
  "take_screenshot",
  "Take a screenshot of your screen and save it as PNG",
  {
    output_path: z.string().optional().describe("Save path e.g. C:\\Users\\R Uma\\Desktop\\screen.png"),
    open_after: z.boolean().optional().default(false),
  },
  async ({ output_path, open_after }) => {
    const savePath = output_path || path.join("C:\\Users\\R Uma\\Desktop", "screenshot_" + Date.now() + ".png");
    await fs.mkdir(path.dirname(savePath), { recursive: true }).catch(() => {});
    const result = await takeScreenshot(savePath);
    if (!result.success) {
      return { content: [{ type: "text", text: `Screenshot failed.\n\n${result.error}` }] };
    }
    const stat = await fs.stat(savePath);
    if (open_after) execAsync(`start "" "${savePath}"`).catch(() => {});
    return {
      content: [{
        type: "text",
        text: `Screenshot saved!\nFile: ${savePath}\nSize: ${(stat.size / 1024).toFixed(1)} KB\nMethod: ${result.method}`,
      }],
    };
  }
);

server.tool(
  "analyze_screenshot",
  "Analyze and describe any image file using Groq Vision AI",
  {
    image_path: z.string().describe("Path to the image file"),
    question: z.string().optional().default("Describe everything you see in this image in detail. Include all text, UI elements, colors, and layout."),
    groq_api_key: z.string().describe("Your free Groq API key from console.groq.com"),
  },
  async ({ image_path, question, groq_api_key }) => {
    try { await fs.access(image_path); } catch {
      return { content: [{ type: "text", text: "File not found: " + image_path }] };
    }
    const ext = path.extname(image_path).toLowerCase();
    if (![".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"].includes(ext)) {
      return { content: [{ type: "text", text: "Not a supported image format." }] };
    }
    const stat = await fs.stat(image_path);
    const base64 = (await fs.readFile(image_path)).toString("base64");
    const description = await groqVision(base64, question, groq_api_key);
    return {
      content: [{
        type: "text",
        text: `IMAGE ANALYSIS\n${"=".repeat(40)}\nFile: ${image_path} (${(stat.size / 1024).toFixed(1)} KB)\n\n${description}`,
      }],
    };
  }
);

server.tool(
  "screenshot_and_analyze",
  "Take a screenshot and immediately show it to Claude for analysis",
  {
    question: z.string().optional().default("Describe everything you see on this screen in detail"),
  },
  async ({ question }) => {
    const savePath = path.join(os.tmpdir(), "mcp_analyze_" + Date.now() + ".png");
    const result = await takeScreenshot(savePath);
    if (!result.success) {
      return { content: [{ type: "text", text: `Could not take screenshot.\n\n${result.error}` }] };
    }
    let imageData;
    try { imageData = await fs.readFile(savePath); } catch {
      return { content: [{ type: "text", text: "Screenshot file was not created. Please try again." }] };
    }
    const base64 = imageData.toString("base64");
    await fs.unlink(savePath).catch(() => {});
    return {
      content: [
        { type: "text", text: `Screenshot captured (${result.method})!\nQuestion: ${question}` },
        { type: "image", data: base64, mimeType: "image/png" },
      ],
    };
  }
);

server.tool(
  "list_screenshots",
  "List all screenshots on your Desktop",
  {},
  async () => {
    const desktop = "C:\\Users\\R Uma\\Desktop";
    try {
      const files = await fs.readdir(desktop);
      const shots = [];
      for (const f of files) {
        if (/\.(png|jpg|jpeg|bmp)$/i.test(f)) {
          const stat = await fs.stat(path.join(desktop, f));
          shots.push(`${f}  —  ${(stat.size / 1024).toFixed(1)} KB  —  ${stat.mtime.toLocaleDateString()}`);
        }
      }
      return {
        content: [{
          type: "text",
          text: shots.length
            ? `Screenshots on Desktop (${shots.length}):\n\n${shots.join("\n")}`
            : "No screenshots found on Desktop.",
        }],
      };
    } catch {
      return { content: [{ type: "text", text: "Could not read Desktop folder." }] };
    }
  }
);

server.tool(
  "smart_screenshot_analyze",
  "Take a screenshot and analyze it using Groq Vision AI (actually sees the screen)",
  {
    question: z.string().optional().default("Describe everything visible on this screen in detail."),
    groq_api_key: z.string().describe("Your free Groq API key from console.groq.com"),
  },
  async ({ question, groq_api_key }) => {
    const savePath = path.join(os.tmpdir(), "mcp_smart_" + Date.now() + ".png");
    let captured = false;
    try {
      const { stdout } = await execAsync(psEncoded(buildSmallScreenshotScript(savePath)), { timeout: 20000 });
      if (stdout.includes("OK")) { await fs.access(savePath); captured = true; }
    } catch {}
    if (!captured) {
      const result = await takeScreenshot(savePath);
      if (!result.success) {
        return { content: [{ type: "text", text: "Screenshot failed: " + result.error }] };
      }
    }
    let imageData;
    try { imageData = await fs.readFile(savePath); } catch {
      return { content: [{ type: "text", text: "Screenshot file not created. Please try again." }] };
    }
    const base64 = imageData.toString("base64");
    await fs.unlink(savePath).catch(() => {});
    const analysis = await groqVision(base64, question, groq_api_key);
    return {
      content: [{
        type: "text",
        text: `SCREEN ANALYSIS (Groq Vision)\n${"=".repeat(40)}\n\n${analysis}`,
      }],
    };
  }
);

server.tool(
  "analyze_image_with_gemini",
  "Analyze any image file using Groq Vision AI (free)",
  {
    image_path: z.string().describe("Full path to image file"),
    question: z.string().optional().default("Describe everything you see in this image in detail."),
    groq_api_key: z.string().describe("Your free Groq API key from console.groq.com"),
  },
  async ({ image_path, question, groq_api_key }) => {
    try { await fs.access(image_path); } catch {
      return { content: [{ type: "text", text: "File not found: " + image_path }] };
    }
    const imageData = await fs.readFile(image_path);
    const base64 = imageData.toString("base64");
    const analysis = await groqVision(base64, question, groq_api_key);
    return {
      content: [{
        type: "text",
        text: `IMAGE ANALYSIS (Groq): ${path.basename(image_path)}\n${"=".repeat(40)}\n\n${analysis}`,
      }],
    };
  }
);

// ─────────────────────────────────────────────
//  RESOURCES & PROMPTS
// ─────────────────────────────────────────────

server.resource("system-info", "system://info", async (uri) => ({
  contents: [{
    uri: uri.href,
    mimeType: "application/json",
    text: JSON.stringify({ platform: os.platform(), arch: os.arch(), node: process.version, hostname: os.hostname(), ram_gb: (os.totalmem() / 1024 ** 3).toFixed(2) }, null, 2),
  }],
}));

server.resource("notes", "notes://all", async (uri) => ({
  contents: [{ uri: uri.href, mimeType: "application/json", text: JSON.stringify(await loadNotes(), null, 2) }],
}));

server.prompt("code-review", "Review code for bugs and improvements", [
  { name: "code", description: "Code to review", required: true },
  { name: "language", description: "Programming language", required: false },
], ({ code, language }) => ({
  messages: [{ role: "user", content: { type: "text", text: "Review this" + (language ? " " + language : "") + " code for bugs, security issues, and improvements:\n\n```\n" + code + "\n```" } }],
}));

server.prompt("explain-code", "Explain what code does step by step", [
  { name: "code", description: "Code to explain", required: true },
], ({ code }) => ({
  messages: [{ role: "user", content: { type: "text", text: "Explain what this code does step by step in simple terms:\n\n```\n" + code + "\n```" } }],
}));

server.prompt("write-tests", "Generate unit tests for a function", [
  { name: "code", description: "Function to test", required: true },
  { name: "framework", description: "Test framework", required: false },
], ({ code, framework }) => ({
  messages: [{ role: "user", content: { type: "text", text: "Write unit tests for this code using " + (framework || "an appropriate framework") + ":\n\n```\n" + code + "\n```" } }],
}));

server.prompt("git-commit-message", "Generate a git commit message from diff", [
  { name: "diff", description: "Git diff output", required: true },
], ({ diff }) => ({
  messages: [{ role: "user", content: { type: "text", text: "Write a conventional commit message (feat/fix/docs/chore) for:\n\n" + diff } }],
}));

server.prompt("debug-error", "Help debug an error", [
  { name: "error", description: "Error message or stack trace", required: true },
  { name: "context", description: "What you were doing", required: false },
], ({ error, context }) => ({
  messages: [{ role: "user", content: { type: "text", text: "Help debug this error" + (context ? " (context: " + context + ")" : "") + ":\n\n```\n" + error + "\n```\n\nWhat is causing it and how to fix it?" } }],
}));

// ─────────────────────────────────────────────
//  START SERVER
// ─────────────────────────────────────────────

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("MCP Server running - All tools ready!");