from __future__ import annotations

import json
import asyncio
import re
from anthropic import AsyncAnthropic
from .tools import execute_tool, TOOL_DEFINITIONS
from .prompts import PLANNING_PROMPT, CHANGE_PROMPT
from db import settings

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

MODEL = "claude-sonnet-4-6"

# Our TOOL_DEFINITIONS already use Anthropic's {name, description, input_schema} format.
ANTHROPIC_TOOLS = TOOL_DEFINITIONS


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
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_iters):
        response = await client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=system_prompt,
            tools=ANTHROPIC_TOOLS,
            messages=messages,
        )

        # No tool use → final answer; pull JSON from the text blocks
        if response.stop_reason != "tool_use":
            text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            parsed = _extract_json(text)
            if parsed is None:
                print("─" * 60)
                print(f"[agent] JSON extraction FAILED")
                print(f"[agent] stop_reason: {response.stop_reason}")
                print(f"[agent] text length: {len(text)} chars")
                print(f"[agent] last 500 chars:\n{text[-500:]}")
                print("─" * 60)
            return parsed

        # Record the assistant turn (text + tool_use blocks) verbatim
        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [block for block in response.content if block.type == "tool_use"]

        # Notify the UI about each tool call
        for tu in tool_uses:
            await queue.put({
                "type": "tool_call",
                "tool": tu.name,
                "message": _label(tu.name, tu.input or {}),
            })

        # Execute all tool calls concurrently
        results = await asyncio.gather(
            *[execute_tool(tu.name, tu.input or {}) for tu in tool_uses],
            return_exceptions=True,
        )

        # Stream results to the UI and feed them back to the model
        tool_result_blocks = []
        for tu, result in zip(tool_uses, results):
            if isinstance(result, Exception):
                result = {"error": str(result)}
            await queue.put({
                "type": "tool_result",
                "tool": tu.name,
                "summary": result.get("summary", "Done") if isinstance(result, dict) else "Done",
            })
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": tool_result_blocks})

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
    response = await client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=prompt,
        messages=[{
            "role": "user",
            "content": (
                f"Conflicts to fix:\n{conflict_desc}\n\n"
                f"Itinerary:\n{json.dumps(itinerary)}"
            ),
        }],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _extract_json(text)
