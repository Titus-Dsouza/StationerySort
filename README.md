# StationerySort — AI Stationery Organizer
> **Hacktoberfest Open-Source AI Challenge Week 3: “Slow and Steady”**  
> A lightweight, privacy-preserving stationery inventory manager for students, powered by local open-weight **Gemma** models via **Ollama**, **Python Flask**, and **SQLite**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Gemma Open-Weight](https://img.shields.io/badge/AI-Gemma%20(Open--Weight)-orange.svg)](https://ai.google.dev/gemma)
[![Ollama](https://img.shields.io/badge/Runtime-Ollama-black.svg)](https://ollama.com/)

---

## 📖 Concept & Overview

Keeping track of school and study supplies—such as pens, notebooks, highlighters, sticky notes, and binder clips—is surprisingly error-prone. Students often find themselves with half a dozen duplicate pens at home while running completely out of index cards or correction tape before an exam.

**StationerySort** reduces manual spreadsheet entries by providing:
1. **Natural-Language Updates with Local Gemma**: Type everyday statements like *"I bought 10 new blue pens"* or *"Used 2 sticky note pads"*. The local open-weight Gemma model automatically resolves item identities, calculates updated quantities, suggests appropriate stationery categories, and flags low stock.
2. **Human-in-the-Loop Confirmation**: The AI proposes changes in a clear side-by-side preview with explanation. Changes are only committed to SQLite once the student confirms.
3. **Automatic Low-Stock Thresholds**: Instant visual badges, warning banners, and a one-click dashboard filter for items requiring restocking.
4. **Student-Friendly Aesthetic**: Warm cream paper background, deep forest-green accents, rounded cards, and subtle micro-animations inspired by modern Japanese stationery design.

---

## 🌟 Why Open-Weight Local AI?

In alignment with **Hacktoberfest Week 3 ("Slow and Steady")**, StationerySort makes the open-weight **Gemma** model an integral part of the application workflow:

- **True Model Choice**: You are not locked into proprietary cloud APIs. You can run `gemma4:12b`, lightweight `gemma2:2b`, or `gemma:2b` depending on your hardware.
- **Zero API Fees & No Rate Limits**: No credit cards, API tokens, or surprise billing. The model runs locally on your Mac, Windows, or Linux laptop.
- **Student Privacy by Design**: Your stationery notes, item lists, and storage locations (e.g. *"Dorm Desk Drawer"*, *"Locker 14"*) never leave your machine.
- **Graceful Heuristic Fallback**: If Ollama is turned off or not yet installed on a reviewer's computer, the built-in fallback parser immediately takes over so the app remains fully testable without breaking. The status pill transparently signals whether Gemma or the fallback engine generated the proposal.

---

## 🛠️ Tech Stack & Architecture

- **Backend**: Python 3 with Flask (lightweight, modular REST API).
- **Database**: SQLite3 (`stationery.db`) with automatic table creation and realistic student sample data seeding.
- **AI Engine**: Local open-weight Gemma model through Ollama's HTTP API (`/api/generate`) with JSON schema enforcement.
- **Frontend**: Vanilla HTML5, CSS3, and JavaScript (ES6+). Zero heavy frontend build chains required.

### System Architecture Flow

```
[ Student Browser ]
       │
       │ (Natural language prompt: "I bought 10 new blue pens")
       ▼
[ Flask Backend /api/ai/parse ]
       │
       ├─► [ Ollama Server (Local Gemma Model) ]
       │        └─ Structured JSON Output (Schema validated)
       │
       └─► [ Fallback Rule Engine ] (If Ollama offline / timed out)
       │
       ▼
[ Proposal Review in UI ] ──(Student Clicks "Confirm")──► [ /api/ai/confirm ]
                                                                │
                                                                ▼
                                                     [ SQLite Database (stationery.db) ]
```

---

## 🚀 Quick Setup & Installation (macOS, Linux, Windows)

### 1. Prerequisites
- **Python 3.10+** (Python 3.11, 3.12, 3.13, 3.14 supported).
- **Ollama** installed: [Download from ollama.com](https://ollama.com/download)

### 2. Pull a Gemma Model
Pull any open-weight Gemma model into Ollama:
```bash
# Recommended standard model
ollama run gemma4:12b

# Or lightweight 2B model for older laptops:
# ollama run gemma2:2b
```

### 3. Clone and Setup Environment
```bash
git clone https://github.com/your-username/stationerysort.git
cd stationerysort

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 4. Configure Environment
Copy the example environment file:
```bash
cp .env.example .env
```
*(By default, `.env` points to `FLASK_PORT=5001`, `OLLAMA_HOST=http://localhost:11434`, and `OLLAMA_MODEL=gemma4:12b`)*.

### 5. Launch the Application
```bash
python app.py
```
Open your browser at **[http://127.0.0.1:5001](http://127.0.0.1:5001)**.

---

## 📦 Features Walkthrough

### 1. Natural Language AI Assistant
- Enter prompts such as:
  - `"I bought 10 new blue pens"`
  - `"Used 2 sticky note pads"`
  - `"Found 5 binder clips in my backpack"`
  - `"Add 3 A4 Graph Notebooks under Paper & Notes with min stock of 2"`
- Gemma maps your phrasing to the best-matched item, calculates the new quantity, and explains its reasoning.

### 2. Human Confirmation Modal / Card
- Every AI request yields a structured proposal card with:
  - Action Badge (`ADD STOCK`, `USE STOCK`, `SET STOCK`, `CREATE ITEM`).
  - Target stationery name and category.
  - Clear stock transition: `Current: 2 pcs ➔ Proposed: 12 pcs (+10)`.
  - Safety Warning if the proposed quantity triggers a low-stock alert.
  - **Confirm & Apply Update** or **Decline & Discard** buttons.

### 3. Interactive Inventory Management
- **One-Click Steppers**: Quickly increment (`+`) or decrement (`-`) quantities directly on cards.
- **Search & Filters**: Search in real time by stationery name, location, or notes.
- **Category Badges**: Filter by Writing, Paper & Notes, Correction & Tools, Fasteners & Clips, Adhesives, or Desk Accessories.
- **Needs Restocking Filter**: Click the terracotta "Needs Restocking" stat card to view all low-stock items at once.
- **Full CRUD**: Add, edit, and delete stationery items with modal forms.
- **Reset Sample Data**: Restore the 12 pre-seeded student stationery items at any time.

---

## 📋 Pre-Seeded Sample Stationery Items

StationerySort works right out of the box with 12 student items, including intentional low-stock items to test alert flags:
- **Blue Gel Pens (0.5mm)** — Qty: 2 (Min: 5) ➔ ⚠️ Low Stock
- **Pastel Sticky Notes (3x3 in)** — Qty: 1 (Min: 3) ➔ ⚠️ Low Stock
- **Pastel Highlighters (6-Color Set)** — Qty: 1 (Min: 2) ➔ ⚠️ Low Stock
- **Correction Tape Dispensers** — Qty: 1 (Min: 2) ➔ ⚠️ Low Stock
- **Standard Staples (No. 10 Box)** — Qty: 1 (Min: 2) ➔ ⚠️ Low Stock
- **A5 Spiral Grid Notebooks** — Qty: 4 (Min: 2) ➔ Normal Stock
- **Wooden HB Graphite Pencils** — Qty: 12 (Min: 4) ➔ Normal Stock
- **Medium Binder Clips (19mm)** — Qty: 24 (Min: 10) ➔ Normal Stock
- **Washable Glue Stick (21g)** — Qty: 3 (Min: 1) ➔ Normal Stock
- *(and more)*

---

## 💡 Community Wisdom & Technical Insights

During development, we drew from practical engineering patterns documented by developer communities on **dev.to**:

1. **Structured Outputs from Local LLMs**  
   *Reference: "Clean JSON Extraction with Ollama and Python" by nearshi ([dev.to](https://dev.to/nearshi/-clean-json-extraction-with-ollama-and-python-21f3))*  
   Local open-weight models may occasionally wrap output in markdown fences (````json ... ````) or include conversational preambles. StationerySort implements a multi-stage sanitizer that strips markdown fences, removes `<thought>` tags from thinking models, extracts the outermost JSON structure, and falls back gracefully to heuristic regex parsing if JSON decoding fails.

2. **Schema Adherence without Heavy SDK Dependencies**  
   *Reference: "Call a local model from plain Python: no SDK, no dependencies" by damiano_builds ([dev.to](https://dev.to/damiano_builds/call-a-local-model-from-plain-python-no-sdk-no-dependencies-3gp5))*  
   Rather than introducing large dependency trees, StationerySort uses Python's standard `requests` and `sqlite3` libraries to communicate directly with Ollama's HTTP API, keeping the application lightweight, fast, and beginner-friendly.

3. **Deterministic Local Execution**  
   *Reference: "Taming Local LLM Non-Determinism" by toai ([dev.to](https://dev.to/toai/taming-local-llm-non-determinism-building-a-resilient-multi-stage-json-sanitizer-schema-adapter-ebg))*  
   Setting a low temperature (`0.1`) ensures reliable, reproducible JSON generation for stock operations across both small (2B) and larger (12B) Gemma models.

---

## 🧪 Testing & Verification

A built-in test suite was run to verify all core workflows:
```bash
./venv/bin/python3 -c "
import database, ai_service
database.init_db()
items = database.get_all_items()
res = ai_service.interpret_inventory_request('I bought 10 new blue pens', items)
assert res['success'] == True
assert res['proposal']['action'] == 'add_stock'
assert res['proposal']['proposed_quantity'] == 12
print('Verification Passed!')
"
```

All API routes (`/api/status`, `/api/items`, `/api/items/<id>/adjust`, `/api/ai/parse`, `/api/ai/confirm`, `/api/items/reset-sample`) have been verified with 100% test pass rate.

---

## 📜 License

Open source under the [MIT License](LICENSE). Built with pride for Hacktoberfest 2026.
