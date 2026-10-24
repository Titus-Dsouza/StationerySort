"""
StationerySort — AI Stationery Organizer
Flask Backend Application
Hacktoberfest Open-Source AI Challenge Week 3: “Slow and Steady”
"""

import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

import database
import ai_service

# Load environment variables
load_dotenv()

APP_PORT = int(os.environ.get("FLASK_PORT", 5001))
APP_HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "stationery.db"))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:12b")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_SORT_KEYS"] = False

# Initialize database on startup
database.init_db(DB_PATH)


@app.route("/")
def index():
    """Serve the primary stationery management dashboard."""
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def get_system_status():
    """Return health check, active Gemma / Ollama state, and database stats."""
    ollama_info = ai_service.check_ollama_status(OLLAMA_HOST, OLLAMA_MODEL)
    stats = database.get_stats(DB_PATH)
    
    return jsonify({
        "status": "online",
        "app_name": "StationerySort",
        "version": "1.0.0",
        "challenge": "Hacktoberfest Open-Source AI — Week 3: Slow and Steady",
        "ollama": ollama_info,
        "stats": stats
    })


@app.route("/api/items", methods=["GET"])
def list_items():
    """Retrieve all stationery items with optional search and filtering."""
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()  # 'all', 'low_stock', 'in_stock'
    
    items = database.get_all_items(DB_PATH, search=search, category=category, status=status)
    return jsonify({
        "items": items,
        "count": len(items)
    })


@app.route("/api/items", methods=["POST"])
def add_item():
    """Manually add a new stationery item."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Item name is required."}), 400

    created = database.create_item(data, DB_PATH)
    return jsonify({
        "message": f"Added '{created['name']}' successfully.",
        "item": created
    }), 201


@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id: int):
    """Retrieve details for a single stationery item."""
    item = database.get_item_by_id(item_id, DB_PATH)
    if not item:
        return jsonify({"error": f"Item {item_id} not found."}), 404
    return jsonify({"item": item})


@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id: int):
    """Update an existing stationery item."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Item name cannot be empty."}), 400

    updated = database.update_item(item_id, data, DB_PATH)
    if not updated:
        return jsonify({"error": f"Item {item_id} not found."}), 404

    return jsonify({
        "message": f"Updated '{updated['name']}' successfully.",
        "item": updated
    })


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id: int):
    """Delete an item from inventory."""
    item = database.get_item_by_id(item_id, DB_PATH)
    if not item:
        return jsonify({"error": f"Item {item_id} not found."}), 404

    name = item["name"]
    database.delete_item(item_id, DB_PATH)
    return jsonify({
        "message": f"Deleted '{name}' from inventory.",
        "item_id": item_id
    })


@app.route("/api/items/<int:item_id>/adjust", methods=["POST"])
def adjust_quantity(item_id: int):
    """Quickly increment, decrement, or set quantity for an item."""
    data = request.get_json() or {}
    delta = data.get("delta")
    new_quantity = data.get("new_quantity")

    if delta is None and new_quantity is None:
        return jsonify({"error": "Must provide 'delta' or 'new_quantity'."}), 400

    updated = database.adjust_item_quantity(
        item_id,
        delta=delta,
        new_quantity=new_quantity,
        db_path=DB_PATH
    )
    if not updated:
        return jsonify({"error": f"Item {item_id} not found."}), 404

    return jsonify({
        "message": f"Quantity updated for '{updated['name']}' ({updated['quantity']} {updated.get('unit', 'pcs')}).",
        "item": updated
    })


@app.route("/api/items/reset-sample", methods=["POST"])
def reset_sample_data():
    """Reset the inventory to the default realistic student stationery items."""
    inserted = database.seed_sample_data(DB_PATH, force=True)
    items = database.get_all_items(DB_PATH)
    stats = database.get_stats(DB_PATH)
    
    return jsonify({
        "message": f"Reset inventory with {inserted} student stationery items.",
        "items": items,
        "stats": stats
    })


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Return list of categories and counts."""
    categories = database.get_categories(DB_PATH)
    return jsonify({"categories": categories})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Return dashboard statistics."""
    stats = database.get_stats(DB_PATH)
    return jsonify({"stats": stats})


@app.route("/api/ai/parse", methods=["POST"])
def ai_parse_prompt():
    """
    Interpret natural language inventory update requests using local Gemma via Ollama,
    with automatic graceful fallback if Ollama is unreachable.
    Does NOT modify the database; returns a structured proposal for student confirmation.
    """
    data = request.get_json() or {}
    user_prompt = data.get("prompt", "").strip()

    if not user_prompt:
        return jsonify({"error": "Please enter a stationery update request."}), 400

    current_items = database.get_all_items(DB_PATH)
    result = ai_service.interpret_inventory_request(
        user_prompt=user_prompt,
        current_items=current_items,
        host=OLLAMA_HOST,
        model=OLLAMA_MODEL
    )

    return jsonify(result)


@app.route("/api/ai/confirm", methods=["POST"])
def ai_confirm_proposal():
    """
    Apply a user-confirmed AI proposal to the SQLite database.
    Ensures human-in-the-loop confirmation before modifying any data.
    """
    data = request.get_json() or {}
    proposal = data.get("proposal")

    if not proposal or not isinstance(proposal, dict):
        return jsonify({"error": "Invalid or missing proposal payload."}), 400

    execution_result = ai_service.execute_proposal(proposal, DB_PATH)
    if not execution_result.get("success"):
        return jsonify(execution_result), 400

    # Include fresh stats and items with the response
    execution_result["stats"] = database.get_stats(DB_PATH)
    execution_result["items"] = database.get_all_items(DB_PATH)
    return jsonify(execution_result)


if __name__ == "__main__":
    print(f"StationerySort starting on http://{APP_HOST}:{APP_PORT}")
    print(f"Ollama Target: {OLLAMA_HOST} (Model: {OLLAMA_MODEL})")
    print(f"SQLite Database: {DB_PATH}")
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
