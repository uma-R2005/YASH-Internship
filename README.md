# 🧠 My MCP Server

A feature-rich **Model Context Protocol (MCP) server** built with Node.js that gives Claude (or any MCP-compatible AI) powerful real-world capabilities — from file management and shell execution to music search, screen capture, and a personal "Second Brain."

---

## ✨ Features at a Glance

| Category | Tools |
|---|---|
| 📁 File System | Read, write, append, delete, move, copy, search, grep |
| 💻 Shell / Code Execution | Run shell commands, Python scripts, Node.js code |
| 🌐 Web / HTTP | Fetch URLs, check status, Wikipedia search, weather, exchange rates |
| 🖥️ System Info | OS info, current time, running processes, disk usage |
| 🔧 Text Utilities | UUID generator, hashing, Base64, word counter, JSON formatter, unit converter, password generator |
| 🎵 Music | Song search (iTunes), lyrics lookup, top charts by genre |
| 📸 Screenshot | Capture screen, analyze images with Groq Vision AI |
| 📝 Notes | Simple key-value note storage and retrieval |
| 🧠 Second Brain | Auto-tagged, auto-connected knowledge base |
| 🔀 Git | Status, log, diff, commit |
| 📧 Email | Send email via Gmail SMTP App Password |
| 🔳 QR Code | Generate QR codes as SVG file or URL |

---

## 🛠️ Tool Reference

### 📁 File System

| Tool | Description |
|---|---|
| `read_file` | Read contents of any file |
| `write_file` | Create or overwrite a file |
| `append_file` | Append text to a file |
| `delete_file` | Delete a file |
| `list_directory` | List files/folders (supports recursive) |
| `move_file` | Move or rename a file |
| `copy_file` | Copy a file to a new location |
| `get_file_info` | Get file metadata (size, dates, type) |
| `search_files` | Find files by name pattern |
| `grep_files` | Search for text content within files |

### 💻 Shell / Code Execution

| Tool | Description |
|---|---|
| `run_command` | Execute any shell command |
| `run_python_code` | Run a Python script inline |
| `run_node_code` | Run a Node.js script inline |
| `get_env_variable` | Read an environment variable |

### 🌐 Web / HTTP

| Tool | Description |
|---|---|
| `fetch_url` | Fetch raw content from a URL |
| `check_url_status` | Check if a URL is reachable |
| `search_wikipedia` | Get a Wikipedia summary |
| `get_public_ip` | Get your public IP address |
| `get_exchange_rates` | Live currency exchange rates |
| `get_weather` | Current weather for any city (Open-Meteo) |
| `get_joke` | Random programming, general, or dad joke |

### 🔧 Utilities

| Tool | Description |
|---|---|
| `generate_uuid` | Generate 1–20 UUIDs |
| `hash_text` | MD5 / SHA1 / SHA256 hash |
| `encode_decode_base64` | Base64 encode or decode |
| `count_words` | Count chars, words, lines, sentences |
| `format_json` | Pretty-print a JSON string |
| `generate_random_password` | Secure password generator |
| `calculate` | Evaluate a math expression |
| `convert_units` | Convert length, weight, temperature, data |

### 🧠 Second Brain

A personal knowledge base that **auto-tags** entries and **auto-connects** related ideas.

| Tool | Description |
|---|---|
| `brain_remember` | Save an idea with auto-tagging and linking |
| `brain_search` | Search memories by keyword or topic |
| `brain_connections` | Explore connections from a memory |
| `brain_map` | View your full knowledge map |
| `brain_forget` | Delete a memory |

Memories are stored locally in `~/.mcp_second_brain.json`.

### 📝 Notes

Simple persistent key-value notes stored in `~/.mcp_notes.json`.

| Tool | Description |
|---|---|
| `save_note` | Save a note by key |
| `get_note` | Retrieve a note by key |
| `list_notes` | List all saved notes |
| `delete_note` | Delete a note by key |

### 🎵 Music

| Tool | Description |
|---|---|
| `search_music` | Search songs via iTunes (artist, album, genre, year) |
| `get_lyrics` | Fetch lyrics for a song |
| `get_top_charts` | Top songs by genre (pop, rock, hip-hop, etc.) |

### 📸 Screenshot & Vision

> Requires a free [Groq API key](https://console.groq.com) for AI image analysis.

| Tool | Description |
|---|---|
| `take_screenshot` | Capture your screen as PNG |
| `analyze_screenshot` | Analyze any image with Groq Vision |
| `screenshot_and_analyze` | Capture + return image inline to Claude |
| `smart_screenshot_analyze` | Capture + analyze with Groq in one step |
| `analyze_image_with_gemini` | Analyze any image file with Groq Vision |
| `list_screenshots` | List all screenshots on your Desktop |

### 📧 Email

Send emails directly via Gmail SMTP using an [App Password](https://myaccount.google.com/apppasswords).

```
First run: npm install nodemailer
```

| Tool | Description |
|---|---|
| `send_email` | Send an email (to, subject, body, from, app password) |
| `setup_email_guide` | Step-by-step Gmail App Password setup guide |

### 🔀 Git

| Tool | Description |
|---|---|
| `git_status` | Get git status for a repo |
| `git_log` | View recent commits |
| `git_diff` | Show uncommitted changes |
| `git_commit` | Stage all and commit with a message |

### 🔳 QR Code

| Tool | Description |
|---|---|
| `generate_qr_code` | Generate a QR code and save as SVG |
| `generate_qr_url` | Get a direct URL to a QR code image |

---
Based on your diagram, here's the complete flow of your MCP server project:

---

## MCP Server Works — Step by Step

**Step 1 — You make a request**
You open MCP Inspector in a browser and type a natural language request, like *"get me the weather."*

**Step 2 — The MCP Server receives it**
Your `index.js` server picks up the request over stdio, understands what's being asked, finds the right tool to handle it, and runs it.

**Step 3 — It routes to the right tool group**
Depending on what you asked, the server dispatches to one of these categories on your machine or over the internet:

- **Your machine** — Files (read/write/search/copy), Shell/Code (run commands, Python, Node), System Info (CPU, RAM, disk, time), Git (status, log, diff, commit), Notes/Memory (save, get, delete), Second Brain (remember and search ideas)
- **Internet** — Web/HTTP (weather, Wikipedia, exchange rates), Music (songs, charts, lyrics), QR Code (generate SVG or URL)
- **AI & Email** — Screenshot + Groq Vision (capture screen, analyze with AI), Email Sender (Gmail SMTP via nodemailer)
- **Utility** — Text tools (UUID, hash, base64, calculate, unit conversion, format JSON)

**Step 4 — The result is packaged**
Once the tool finishes executing, the result is wrapped as plain text and sent back over stdio to the server.

**Step 5 — You see the answer**
MCP Inspector displays the final result — for example, *"Hyderabad: 34°C, Clear sky."*

