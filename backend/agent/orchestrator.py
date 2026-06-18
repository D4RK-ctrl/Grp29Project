from __future__ import annotations

import json
import asyncio
import re
import httpx
import logging
from .tools import execute_tool, TOOL_DEFINITIONS
from .prompts import PLANNING_PROMPT, CHANGE_PROMPT
from db import settings

logger = logging.getLogger(__name__)

def convert_to_openai_tools(anthropic_tools: list) -> list:
    openai_tools = []
    for tool in anthropic_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool.get("input_schema", {})
            }
        })
    return openai_tools

OPENAI_TOOLS = convert_to_openai_tools(TOOL_DEFINITIONS)


async def call_llm_api(
    messages: list,
    tools: list = None,
    json_mode: bool = False,
) -> dict:
    """Calls any OpenAI-compatible API (like Groq, OpenRouter, OpenAI, etc.) with retry and backoff."""
    api_key = settings.LLM_API_KEY
    base_url = settings.LLM_BASE_URL.rstrip('/')
    model = settings.LLM_MODEL
    
    url = f"{base_url}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
    }
    
    if tools:
        payload["tools"] = tools
        
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
        
    backoff = 2.0
    max_retries = 5
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(max_retries):
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    print(f"[LLM API] 429 Rate Limited. Retrying in {backoff}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                elif resp.status_code >= 500:
                    print(f"[LLM API] Server Error {resp.status_code}. Retrying in {backoff}s... (Attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                else:
                    print(f"[LLM API] HTTP {resp.status_code}: {resp.text}")
                    resp.raise_for_status()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"[LLM API] Error: {e}. Retrying in {backoff}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(backoff)
                backoff *= 2.0
                
    raise Exception("Max retries exceeded calling LLM API")


_TOOL_LABELS = {
    "search_flights": lambda p: f"Searching flights {p.get('origin','')} → {p.get('destination','')} on {p.get('departure_date','')}",
    "search_hotels": lambda p: f"Finding hotels in {p.get('city_code','')} ({p.get('checkin_date','')} – {p.get('checkout_date','')})",
    "search_activities": lambda p: f"Discovering {p.get('category','attractions')} in {p.get('city','')}",
    "search_restaurants": lambda p: f"Finding restaurants in {p.get('location','')}",
    "get_weather": lambda p: f"Checking weather for {p.get('city','')}",
    "web_search": lambda p: f"Searching: {p.get('query','')}",
}


def _label(tool_name: str, params: dict) -> str:
    fn = _TOOL_LABELS.get(tool_name)
    return fn(params) if fn else f"Running {tool_name}"


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except Exception:
            pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


def _safe_args(raw: str) -> dict:
    try:
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


async def _agent_loop(
    system_prompt: str,
    user_message: str,
    queue: asyncio.Queue,
    max_iters: int = 20,
) -> dict | None:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    for _ in range(max_iters):
        response = await call_llm_api(
            messages=messages,
            tools=OPENAI_TOOLS,
        )

        choices = response.get("choices", [])
        if not choices:
            raise Exception("No choices returned from LLM API")

        choice = choices[0]
        choice_message = choice.get("message", {})
        content = choice_message.get("content") or ""
        tool_calls = choice_message.get("tool_calls") or []

        # No tool use → final answer; pull JSON from the text
        if not tool_calls:
            parsed = _extract_json(content)
            if parsed is None:
                print("─" * 60)
                print(f"[agent] JSON extraction FAILED")
                print(f"[agent] text length: {len(content)} chars")
                print(f"[agent] last 500 chars:\n{content[-500:]}")
                print("─" * 60)
            return parsed

        # Record assistant's turn in messages history
        messages.append(choice_message)

        # Notify UI about tool calls
        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")
            args = _safe_args(func.get("arguments", ""))
            await queue.put({
                "type": "tool_call",
                "tool": name,
                "message": _label(name, args),
            })

        # Execute concurrently
        results = await asyncio.gather(
            *[
                execute_tool(
                    tc.get("function", {}).get("name", ""),
                    _safe_args(tc.get("function", {}).get("arguments", ""))
                )
                for tc in tool_calls
            ],
            return_exceptions=True,
        )

        # Stream result and feed it back to LLM
        for tc, result in zip(tool_calls, results):
            func = tc.get("function", {})
            name = func.get("name", "")
            if isinstance(result, Exception):
                result = {"error": str(result)}
            await queue.put({
                "type": "tool_result",
                "tool": name,
                "summary": result.get("summary", "Done") if isinstance(result, dict) else "Done",
            })
            
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "name": name,
                "content": json.dumps(result)
            })

    return None


async def run_planning_agent(brief: str, trip_id: str, queue: asyncio.Queue) -> dict | None:
    await queue.put({"type": "status", "message": "Understanding your travel brief..."})

    itinerary = await _agent_loop(
        system_prompt=PLANNING_PROMPT,
        user_message=f"Plan a complete trip based on this brief:\n\n{brief}",
        queue=queue,
    )

    if itinerary:
        await queue.put({"type": "status", "message": "Checking for scheduling conflicts..."})
        conflicts = _check_conflicts(itinerary)
        if conflicts:
            itinerary["conflicts"] = conflicts
            await queue.put({
                "type": "status",
                "message": f"Found {len(conflicts)} conflict(s) — resolving automatically...",
            })
            itinerary = await _resolve_conflicts(itinerary, conflicts, queue) or itinerary
        else:
            itinerary["conflicts"] = []

        await queue.put({"type": "complete", "itinerary": itinerary})
    else:
        await queue.put({"type": "error", "message": "Agent failed to generate itinerary. Please try again."})

    return itinerary


async def run_change_agent(
    existing_itinerary: dict,
    change_request: str,
    queue: asyncio.Queue,
) -> dict | None:
    await queue.put({"type": "status", "message": "Analysing impact of your change..."})

    user_message = (
        f"Change request: {change_request}\n\n"
        f"Current itinerary:\n{json.dumps(existing_itinerary, indent=2)}"
    )

    revised = await _agent_loop(
        system_prompt=CHANGE_PROMPT,
        user_message=user_message,
        queue=queue,
    )

    if revised:
        conflicts = _check_conflicts(revised)
        revised["conflicts"] = conflicts if conflicts else []
        await queue.put({"type": "complete", "itinerary": revised})
    else:
        await queue.put({"type": "error", "message": "Failed to process change. Please try again."})

    return revised


def _check_conflicts(itinerary: dict) -> list[dict]:
    conflicts = []

    def to_minutes(t: str) -> int:
        try:
            parts = t.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            return -1

    for day in itinerary.get("days", []):
        events = sorted(
            [e for e in day.get("events", []) if e.get("time")],
            key=lambda e: to_minutes(e["time"]),
        )
        for i in range(len(events) - 1):
            curr = events[i]
            nxt = events[i + 1]
            curr_end = curr.get("end_time") or curr["time"]
            curr_end_min = to_minutes(curr_end)
            nxt_start_min = to_minutes(nxt["time"])
            if curr_end_min > nxt_start_min and curr_end_min != -1 and nxt_start_min != -1:
                conflicts.append({
                    "day": day["date"],
                    "type": "overlap",
                    "event1": curr["title"],
                    "event1_end": curr_end,
                    "event2": nxt["title"],
                    "event2_start": nxt["time"],
                    "description": (
                        f"'{curr['title']}' ends at {curr_end} but "
                        f"'{nxt['title']}' starts at {nxt['time']}"
                    ),
                })
    return conflicts


async def _resolve_conflicts(
    itinerary: dict,
    conflicts: list[dict],
    queue: asyncio.Queue,
) -> dict | None:
    """Fix timing overlaps with a single, tool-free LLM call. Conflicts are
    scheduling issues — they need no web searches, just a quick reshuffle."""
    conflict_desc = "\n".join(f"- {c['description']}" for c in conflicts)
    prompt = (
        "You are fixing scheduling conflicts in a travel itinerary. "
        "Adjust ONLY the event times to remove the overlaps below. "
        "Do not search for anything. Keep everything else identical. "
        "Add a 'changes_summary' field describing what you moved. "
        "Return ONLY the complete corrected JSON itinerary, no prose."
    )
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Conflicts to fix:\n{conflict_desc}\n\n"
                f"Itinerary:\n{json.dumps(itinerary)}"
            )
        }
    ]
    response = await call_llm_api(
        messages=messages,
        json_mode=True,
    )
    choices = response.get("choices", [])
    if not choices:
        return None
    content = choices[0].get("message", {}).get("content") or ""
    return _extract_json(content)
