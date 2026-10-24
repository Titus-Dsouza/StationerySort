"""
StationerySort — AI Service Layer
Integrates local open-weight Gemma models via Ollama with robust JSON extraction
and an intelligent graceful fallback rule engine when Ollama is offline or unavailable.
"""

import json
import re
import requests
import os
from typing import Dict, Any, List, Optional, Tuple

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:12b")
DEFAULT_OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "40.0"))

STANDARD_CATEGORIES = [
    "Writing",
    "Paper & Notes",
    "Correction & Tools",
    "Fasteners & Clips",
    "Adhesives",
    "Desk Accessories"
]

def check_ollama_status(host: str = DEFAULT_OLLAMA_HOST, target_model: str = DEFAULT_OLLAMA_MODEL) -> Dict[str, Any]:
    """Check whether Ollama is running and which models are installed."""
    try:
        url = f"{host.rstrip('/')}/api/tags"
        resp = requests.get(url, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name") for m in data.get("models", [])]
            
            # Check if target_model is present, or find best gemma match
            has_target = any(target_model in m for m in models)
            gemma_models = [m for m in models if "gemma" in m.lower()]
            
            active_model = target_model if has_target else (gemma_models[0] if gemma_models else (models[0] if models else target_model))
            
            return {
                "available": True,
                "host": host,
                "active_model": active_model,
                "target_model_installed": has_target,
                "all_models": models,
                "gemma_models": gemma_models,
                "message": f"Connected to Ollama ({active_model})"
            }
    except Exception:
        pass
    
    return {
        "available": False,
        "host": host,
        "active_model": target_model,
        "target_model_installed": False,
        "all_models": [],
        "gemma_models": [],
        "message": f"Ollama not reachable at {host}. Fallback active."
    }

def clean_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Clean markdown code fences, Ollama thinking tokens, and parse JSON safely."""
    if not raw_text:
        return None
        
    text = raw_text.strip()
    
    # Strip <thought>...</thought> tags if present in thinking models
    text = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL).strip()
    
    # Strip markdown ```json ... ``` code blocks
    if "```" in text:
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        else:
            text = re.sub(r'^```(?:json)?', '', text).strip()
            text = re.sub(r'```$', '', text).strip()

    # Find outermost curly braces if there is preamble or epilogue text
    brace_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if brace_match:
        text = brace_match.group(1).strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return None

def normalize_action(raw_action: str) -> str:
    """Normalize action string to one of standard verbs."""
    a = str(raw_action).lower().strip()
    if any(k in a for k in ["add", "buy", "bought", "purchas", "restock", "found", "receiv", "got"]):
        return "add_stock"
    if any(k in a for k in ["use", "used", "deduct", "consum", "spent", "lost", "took", "finish"]):
        return "use_stock"
    if any(k in a for k in ["set", "reset", "exact", "count"]):
        return "set_stock"
    if any(k in a for k in ["delete", "remove", "discard"]):
        return "delete_item"
    if any(k in a for k in ["create", "new"]):
        return "create_item"
    return "add_stock"

def build_gemma_prompt(user_prompt: str, current_items: List[Dict[str, Any]]) -> str:
    """Construct a concise prompt for Gemma to parse inventory actions."""
    items_summary = "\n".join([
        f"- ID {item['id']}: {item['name']} (Category: {item['category']}, Qty: {item['quantity']})"
        for item in current_items
    ])
    
    prompt = f"""You are the StationerySort AI assistant. A student said: "{user_prompt}"

INVENTORY LIST:
{items_summary}

Analyze the request. Match to an existing item ID if applicable, or set matched_item_id to null if it is a new item.
Respond ONLY with this JSON schema:
{{
  "action": "add_stock" or "use_stock" or "set_stock" or "create_item" or "delete_item",
  "item_name": "best matched or new item name",
  "matched_item_id": id_number_or_null,
  "category": "Writing" or "Paper & Notes" or "Correction & Tools" or "Fasteners & Clips" or "Adhesives" or "Desk Accessories",
  "quantity_delta": integer,
  "proposed_quantity": integer,
  "min_stock_level": integer,
  "explanation": "concise friendly 1-sentence explanation"
}}
JSON:"""
    return prompt

def parse_with_gemma(
    user_prompt: str,
    current_items: List[Dict[str, Any]],
    host: str = DEFAULT_OLLAMA_HOST,
    model: str = DEFAULT_OLLAMA_MODEL,
    timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT
) -> Optional[Dict[str, Any]]:
    """Send natural language request to Ollama running Gemma and extract structured proposal."""
    try:
        url = f"{host.rstrip('/')}/api/generate"
        prompt = build_gemma_prompt(user_prompt, current_items)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }
        
        resp = requests.post(url, json=payload, timeout=timeout_seconds)
        if resp.status_code == 200:
            res_data = resp.json()
            raw_response = res_data.get("response", "")
            proposal = clean_json_response(raw_response)
            
            if proposal and ("action" in proposal or "item_name" in proposal):
                action = normalize_action(proposal.get("action", "add_stock"))
                    
                matched_id = proposal.get("matched_item_id")
                if matched_id is not None:
                    try:
                        matched_id = int(matched_id)
                        matching_item = next((it for it in current_items if it["id"] == matched_id), None)
                        if not matching_item:
                            matched_id = None
                    except (ValueError, TypeError):
                        matched_id = None
                
                # If matched_id is None, try fuzzy matching item_name against current_items
                item_name = str(proposal.get("item_name", "")).strip()
                if not matched_id and item_name:
                    for it in current_items:
                        if item_name.lower() in it["name"].lower() or it["name"].lower() in item_name.lower():
                            matched_id = it["id"]
                            break

                current_qty = 0
                unit = str(proposal.get("unit", "pcs")).strip() or "pcs"
                min_stock = int(proposal.get("min_stock_level", 2) or 2)
                category = str(proposal.get("category", "Writing")).strip() or "Writing"
                
                if matched_id:
                    matched_obj = next(it for it in current_items if it["id"] == matched_id)
                    current_qty = matched_obj["quantity"]
                    if not item_name or len(item_name) < 3:
                        item_name = matched_obj["name"]
                    category = matched_obj["category"]
                    min_stock = matched_obj["min_stock_level"]
                    unit = matched_obj.get("unit", unit)

                delta = int(proposal.get("quantity_delta", 1) or 1)
                
                # Compute proposed quantity reliably
                if action == "add_stock":
                    delta = abs(delta)
                    proposed_qty = current_qty + delta
                elif action == "use_stock":
                    delta = abs(delta)
                    proposed_qty = max(0, current_qty - delta)
                elif action == "set_stock":
                    proposed_qty = max(0, int(proposal.get("proposed_quantity", current_qty) or 0))
                    delta = proposed_qty - current_qty
                elif action == "create_item":
                    proposed_qty = max(0, int(proposal.get("proposed_quantity", delta) or delta))
                elif action == "delete_item":
                    proposed_qty = 0
                else:
                    proposed_qty = current_qty

                return {
                    "action": action,
                    "item_name": item_name or "Stationery Item",
                    "matched_item_id": matched_id,
                    "category": category,
                    "current_quantity": current_qty,
                    "quantity_delta": delta,
                    "proposed_quantity": proposed_qty,
                    "min_stock_level": min_stock,
                    "unit": unit,
                    "explanation": proposal.get("explanation", f"Gemma identified '{action}' for {item_name}."),
                    "ai_source": f"ollama:{model}",
                    "confidence": "high"
                }
    except Exception:
        # Fallback to rule engine on any error or timeout
        pass
    return None

def guess_category(text: str) -> str:
    """Heuristic category classification for student stationery items."""
    t = text.lower()
    if any(k in t for k in ["pen", "pencil", "highlighter", "marker", "sharpie", "ink", "lead", "fineliner", "gel", "ballpoint"]):
        return "Writing"
    if any(k in t for k in ["note", "paper", "sticky", "notebook", "pad", "index", "tab", "flag", "flashcard", "folder", "binder"]):
        return "Paper & Notes"
    if any(k in t for k in ["eraser", "rubber", "correction", "whited-out", "whiteout", "ruler", "scale", "scissor", "cutter"]):
        return "Correction & Tools"
    if any(k in t for k in ["clip", "staple", "stapler", "pin", "binder clip", "paperclip", "rubber band", "fastener"]):
        return "Fasteners & Clips"
    if any(k in t for k in ["glue", "tape", "washi", "adhesive", "stick", "gum"]):
        return "Adhesives"
    return "Desk Accessories"

def fallback_rule_parser(user_prompt: str, current_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Intelligent heuristic fallback when Ollama is offline or Gemma is unreachable.
    Accurately parses natural language phrases like 'I bought 10 new blue pens',
    'Used 2 sticky note pads', 'Set pencils to 20', etc.
    """
    p = user_prompt.strip()
    p_lower = p.lower()
    
    # 1. Detect Intent / Action
    action = "add_stock"
    if any(w in p_lower for w in ["used", "use", "spent", "consumed", "finished", "ran out", "lost", "took", "discarded"]):
        action = "use_stock"
    elif any(w in p_lower for w in ["set", "reset", "now have", "count is", "total is", "have exactly"]):
        action = "set_stock"
    elif any(w in p_lower for w in ["delete", "remove", "throw away", "get rid of"]) and not any(w in p_lower for w in ["from", "units"]):
        action = "delete_item"
    elif any(w in p_lower for w in ["bought", "buy", "purchased", "got", "found", "received", "added", "restocked", "new"]):
        action = "add_stock"
    elif any(w in p_lower for w in ["create", "add new item"]):
        action = "create_item"

    # 2. Extract number / quantity
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "dozen": 12, "twenty": 20
    }
    extracted_qty = None
    
    # Check digits first
    digits_match = re.search(r'\b(\d+)\b', p)
    if digits_match:
        extracted_qty = int(digits_match.group(1))
    else:
        # Check words
        for word, val in number_words.items():
            if re.search(rf'\b{word}\b', p_lower):
                extracted_qty = val
                break
    
    if extracted_qty is None:
        extracted_qty = 1  # default 1 if singular (e.g. "bought a blue pen")

    # 3. Match against existing inventory items
    best_match = None
    best_score = 0

    clean_prompt = re.sub(r'\b(i|bought|buy|got|found|used|use|set|to|added|new|a|an|the|my|in|at|units?|pieces?|pcs|pads?|box|packs?)\b', '', p_lower)
    prompt_tokens = set(re.findall(r'\w+', clean_prompt))

    for item in current_items:
        name_lower = item["name"].lower()
        item_tokens = set(re.findall(r'\w+', name_lower))
        
        # Exact substring match
        if any(token in name_lower for token in prompt_tokens if len(token) > 2):
            overlap = len(prompt_tokens.intersection(item_tokens))
            score = overlap * 2
            if any(token in name_lower for token in ["pen", "pencil", "sticky", "eraser", "clip", "tape", "notebook", "ruler", "staple"]):
                # specific stationery keywords
                for kw in ["pen", "pencil", "sticky", "eraser", "clip", "tape", "notebook", "ruler", "staple", "highlighter"]:
                    if kw in p_lower and kw in name_lower:
                        score += 3
            if score > best_score:
                best_score = score
                best_match = item

    # 4. Determine item name, category, and quantities
    matched_id = None
    current_qty = 0
    unit = "pcs"
    min_stock = 2

    if best_match and best_score >= 2:
        matched_id = best_match["id"]
        item_name = best_match["name"]
        category = best_match["category"]
        current_qty = best_match["quantity"]
        unit = best_match.get("unit", "pcs")
        min_stock = best_match["min_stock_level"]
    else:
        # Not matched, either create new item or fallback
        # Try extracting meaningful name from prompt
        name_candidate = clean_prompt.strip()
        # Capitalize candidate
        name_candidate = " ".join(w.capitalize() for w in name_candidate.split() if len(w) > 1)
        if not name_candidate:
            name_candidate = "New Stationery Item"
        item_name = name_candidate
        category = guess_category(p)
        action = "create_item" if action in ["add_stock", "create_item"] else action

    delta = extracted_qty
    if action == "add_stock":
        proposed_qty = current_qty + delta
        explanation = f"Fallback rule engine detected purchase/restock: adding {delta} {unit} to '{item_name}' (Current: {current_qty} ➔ Proposed: {proposed_qty})."
    elif action == "use_stock":
        proposed_qty = max(0, current_qty - delta)
        explanation = f"Fallback rule engine detected usage: deducting {delta} {unit} from '{item_name}' (Current: {current_qty} ➔ Proposed: {proposed_qty})."
    elif action == "set_stock":
        proposed_qty = delta
        delta = proposed_qty - current_qty
        explanation = f"Fallback rule engine detected direct count: setting '{item_name}' to {proposed_qty} {unit}."
    elif action == "create_item":
        proposed_qty = delta
        matched_id = None
        explanation = f"Fallback rule engine proposed creating new stationery item '{item_name}' in category '{category}' with quantity {proposed_qty} {unit}."
    elif action == "delete_item":
        proposed_qty = 0
        explanation = f"Fallback rule engine proposed removing item '{item_name}' from inventory."
    else:
        proposed_qty = current_qty
        explanation = f"Processed request for '{item_name}'."

    return {
        "action": action,
        "item_name": item_name,
        "matched_item_id": matched_id,
        "category": category,
        "current_quantity": current_qty,
        "quantity_delta": delta,
        "proposed_quantity": proposed_qty,
        "min_stock_level": min_stock,
        "unit": unit,
        "explanation": explanation,
        "ai_source": "fallback_rule_engine",
        "confidence": "medium"
    }

def interpret_inventory_request(
    user_prompt: str,
    current_items: List[Dict[str, Any]],
    host: str = DEFAULT_OLLAMA_HOST,
    model: str = DEFAULT_OLLAMA_MODEL
) -> Dict[str, Any]:
    """
    Primary entry point: Attempts open-weight Gemma model through Ollama first;
    gracefully falls back to heuristic rule engine if Ollama is unavailable or times out.
    """
    if not user_prompt or not user_prompt.strip():
        return {
            "success": False,
            "error": "Please provide an inventory update request.",
            "proposal": None
        }

    status = check_ollama_status(host, model)
    active_model = status.get("active_model", model)
    
    proposal = None
    if status["available"]:
        proposal = parse_with_gemma(user_prompt, current_items, host, active_model)

    if not proposal:
        # Graceful fallback triggered
        proposal = fallback_rule_parser(user_prompt, current_items)

    # Check if proposed quantity triggers low-stock warning
    is_proposed_low_stock = proposal["proposed_quantity"] <= proposal["min_stock_level"]
    proposal["is_low_stock_warning"] = is_proposed_low_stock

    return {
        "success": True,
        "ollama_connected": status["available"],
        "active_model": active_model,
        "ai_source": proposal.get("ai_source", "unknown"),
        "proposal": proposal
    }

def execute_proposal(proposal: Dict[str, Any], db_path: str) -> Dict[str, Any]:
    """Execute the user-confirmed proposal in SQLite database."""
    import database
    action = proposal.get("action", "add_stock")
    matched_id = proposal.get("matched_item_id")
    proposed_qty = max(0, int(proposal.get("proposed_quantity", 0)))
    
    if action in ["add_stock", "use_stock", "set_stock"] and matched_id:
        updated = database.adjust_item_quantity(matched_id, new_quantity=proposed_qty, db_path=db_path)
        if updated:
            return {
                "success": True,
                "action": action,
                "message": f"Successfully updated '{updated['name']}' to {updated['quantity']} {updated.get('unit', 'pcs')}.",
                "item": updated
            }
        else:
            return {"success": False, "error": f"Item with ID {matched_id} not found."}
            
    elif action == "create_item" or (action in ["add_stock", "set_stock"] and not matched_id):
        new_data = {
            "name": proposal.get("item_name", "New Stationery Item").strip(),
            "category": proposal.get("category", "General").strip(),
            "quantity": proposed_qty,
            "min_stock_level": int(proposal.get("min_stock_level", 2)),
            "unit": proposal.get("unit", "pcs").strip() or "pcs",
            "location": proposal.get("location", "Desk").strip() or "Desk",
            "notes": f"Created via AI: {proposal.get('explanation', '')}".strip()
        }
        created = database.create_item(new_data, db_path=db_path)
        return {
            "success": True,
            "action": "create_item",
            "message": f"Created new item '{created['name']}' in category '{created['category']}' with {created['quantity']} {created.get('unit', 'pcs')}.",
            "item": created
        }
        
    elif action == "delete_item" and matched_id:
        item = database.get_item_by_id(matched_id, db_path=db_path)
        item_name = item["name"] if item else "Item"
        deleted = database.delete_item(matched_id, db_path=db_path)
        if deleted:
            return {
                "success": True,
                "action": "delete_item",
                "message": f"Successfully removed '{item_name}' from inventory.",
                "item_id": matched_id
            }
        else:
            return {"success": False, "error": f"Failed to delete item {matched_id}."}
            
    return {"success": False, "error": f"Unrecognized action '{action}' or missing item target."}

