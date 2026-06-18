import httpx
import asyncio
import json
from db import settings


# ── Tool: search_flights (via Tavily web search) ─────────────────────────────
async def _search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int,
    return_date: str = None,
    currency: str = "USD",
) -> dict:
    query = f"flights from {origin} to {destination} on {departure_date} {adults} passengers price USD airline options"
    r = await _web_search(query, max_results=5)
    results = r.get("results", [])

    summary = (
        f"Found web results for flights {origin}→{destination} on {departure_date} "
        f"for {adults} passenger(s). "
        f"Agent will extract options from search results."
    )
    return {
        "summary": summary,
        "search_results": results[:6],
        "search_tip": (
            f"Search for flights {origin} to {destination} on {departure_date}. "
            f"Extract airline names, prices, departure/arrival times, and number of stops "
            f"from the snippets. Typical routes and price ranges are in the results."
        ),
    }


# ── Tool: search_hotels (via Tavily web search) ───────────────────────────────
async def _search_hotels(
    city_code: str,
    checkin_date: str,
    checkout_date: str,
    adults: int,
    budget_per_night: float = None,
) -> dict:
    budget_str = f"under ${int(budget_per_night)} per night" if budget_per_night else "best value"
    query = f"best hotels in {city_code} {checkin_date} to {checkout_date} {adults} guests {budget_str} price per night"
    r = await _web_search(query, max_results=5)
    results = r.get("results", [])

    summary = (
        f"Found web results for hotels in {city_code} "
        f"({checkin_date} – {checkout_date}), {adults} guest(s)."
    )
    return {
        "summary": summary,
        "search_results": results[:6],
        "search_tip": (
            f"Extract hotel names, star ratings, price per night, amenities, "
            f"and check-in/check-out times from the search snippets for {city_code}."
        ),
    }


# ── Tool: search_activities ───────────────────────────────────────────────────
async def _search_activities(city: str, category: str = None, limit: int = 10) -> dict:
    try:
        if not settings.FOURSQUARE_API_KEY:
            raise ValueError("No Foursquare key")

        query = category if category else "tourist attractions"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.foursquare.com/v3/places/search",
                headers={
                    "Authorization": settings.FOURSQUARE_API_KEY,
                    "Accept": "application/json",
                },
                params={"near": city, "query": query, "limit": limit, "sort": "RATING"},
            )
            resp.raise_for_status()
            raw = resp.json()

        activities = []
        for place in raw.get("results", []):
            cats = place.get("categories", [{}])
            activities.append({
                "name": place["name"],
                "category": cats[0].get("name", "Attraction") if cats else "Attraction",
                "address": place.get("location", {}).get("formatted_address", ""),
                "rating": round(place.get("rating", 7.0) / 2, 1),
                "price": 0,
                "duration_hours": 2,
                "description": f"Popular {cats[0].get('name', 'attraction')} in {city}" if cats else "",
            })

        return {
            "summary": f"Found {len(activities)} {category or 'attractions'} in {city}",
            "activities": activities,
        }

    except Exception:
        r = await _web_search(f"top tourist attractions things to do in {city} {category or ''} must visit")
        return {
            "summary": f"Found web results for activities in {city}",
            "activities": [],
            "search_results": r.get("results", []),
        }


# ── Tool: search_restaurants ──────────────────────────────────────────────────
async def _search_restaurants(
    location: str, cuisine: str = None, price_range: str = "mid-range", limit: int = 6
) -> dict:
    try:
        if not settings.YELP_API_KEY:
            raise ValueError("No Yelp key")

        price_map = {"budget": "1", "mid-range": "1,2", "upscale": "3,4"}
        term = f"{cuisine} restaurants" if cuisine else "restaurants"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.yelp.com/v3/businesses/search",
                headers={"Authorization": f"Bearer {settings.YELP_API_KEY}"},
                params={
                    "location": location,
                    "term": term,
                    "limit": limit,
                    "sort_by": "rating",
                    "price": price_map.get(price_range, "1,2"),
                },
            )
            resp.raise_for_status()
            raw = resp.json()

        restaurants = []
        for biz in raw.get("businesses", []):
            cats = biz.get("categories", [{}])
            restaurants.append({
                "name": biz["name"],
                "cuisine": cats[0].get("title", "Local") if cats else "Local",
                "address": biz.get("location", {}).get("display_address", [""])[0],
                "rating": biz.get("rating", 4.0),
                "price": biz.get("price", "$$"),
                "review_count": biz.get("review_count", 0),
                "url": biz.get("url", ""),
            })

        return {
            "summary": f"Found {len(restaurants)} restaurants in {location}",
            "restaurants": restaurants,
        }

    except Exception:
        r = await _web_search(f"best {cuisine or ''} restaurants in {location} must try")
        return {
            "summary": f"Found web results for restaurants in {location}",
            "restaurants": [],
            "search_results": r.get("results", []),
        }


# ── Tool: get_weather ─────────────────────────────────────────────────────────
async def _get_weather(city: str, start_date: str, end_date: str) -> dict:
    try:
        if not settings.OPENWEATHER_API_KEY:
            raise ValueError("No OWM key")

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={
                    "q": city,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "metric",
                    "cnt": 40,
                },
            )
            resp.raise_for_status()
            raw = resp.json()

        daily: dict = {}
        for item in raw.get("list", []):
            date = item["dt_txt"][:10]
            if date < start_date or date > end_date:
                continue
            if date not in daily:
                daily[date] = {"temps": [], "descriptions": [], "humidity": []}
            daily[date]["temps"].append(item["main"]["temp"])
            daily[date]["descriptions"].append(item["weather"][0]["description"])
            daily[date]["humidity"].append(item["main"]["humidity"])

        result_days = [
            {
                "date": date,
                "temp_high": round(max(d["temps"])),
                "temp_low": round(min(d["temps"])),
                "description": d["descriptions"][0].capitalize(),
                "humidity": round(sum(d["humidity"]) / len(d["humidity"])),
            }
            for date, d in sorted(daily.items())
        ]

        avg_high = round(sum(d["temp_high"] for d in result_days) / len(result_days)) if result_days else 25
        return {
            "summary": f"Avg high {avg_high}°C. {result_days[0]['description'] if result_days else 'Check local forecast'}",
            "daily": result_days,
        }

    except Exception:
        r = await _web_search(f"weather in {city} in {start_date[:7]} average temperature forecast")
        return {
            "summary": "Weather data from web search",
            "daily": [],
            "search_results": r.get("results", []),
        }


# ── Tool: web_search ──────────────────────────────────────────────────────────
async def _web_search(query: str, max_results: int = 5) -> dict:
    try:
        if not settings.TAVILY_API_KEY:
            return {"summary": "Web search unavailable (no Tavily key)", "results": []}

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "basic",
                },
            )
            resp.raise_for_status()
            raw = resp.json()

        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:400],
            }
            for r in raw.get("results", [])
        ]
        return {"summary": f"Found {len(results)} results for: {query}", "results": results}

    except Exception as e:
        return {"summary": f"Web search failed: {e}", "results": []}


# ── Dispatcher + Tool definitions ─────────────────────────────────────────────
_TOOL_MAP = {
    "search_flights": _search_flights,
    "search_hotels": _search_hotels,
    "search_activities": _search_activities,
    "search_restaurants": _search_restaurants,
    "get_weather": _get_weather,
    "web_search": _web_search,
}


async def execute_tool(name: str, params: dict) -> dict:
    func = _TOOL_MAP.get(name)
    if not func:
        return {"error": f"Unknown tool: {name}"}
    try:
        return await func(**params)
    except Exception as e:
        return {"error": str(e), "tool": name}


TOOL_DEFINITIONS = [
    {
        "name": "search_flights",
        "description": "Search the web for available flights between two airports. Returns real search results with airline options, prices, and schedules.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "IATA airport code (e.g. JFK, LHR)"},
                "destination": {"type": "string", "description": "IATA airport code (e.g. BKK, CDG)"},
                "departure_date": {"type": "string", "description": "YYYY-MM-DD"},
                "adults": {"type": "integer", "description": "Number of adult passengers"},
                "return_date": {"type": "string", "description": "YYYY-MM-DD for return leg"},
                "currency": {"type": "string", "description": "Currency code, default USD"},
            },
            "required": ["origin", "destination", "departure_date", "adults"],
        },
    },
    {
        "name": "search_hotels",
        "description": "Search the web for available hotels in a city with real prices and ratings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city_code": {"type": "string", "description": "City name or IATA code (e.g. Bangkok, BKK)"},
                "checkin_date": {"type": "string", "description": "YYYY-MM-DD"},
                "checkout_date": {"type": "string", "description": "YYYY-MM-DD"},
                "adults": {"type": "integer", "description": "Number of guests"},
                "budget_per_night": {"type": "number", "description": "Max price per night USD (optional)"},
            },
            "required": ["city_code", "checkin_date", "checkout_date", "adults"],
        },
    },
    {
        "name": "search_activities",
        "description": "Find tourist attractions, museums, temples, tours, and experiences in a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "category": {"type": "string", "description": "Type: museum, temple, outdoor, market, nightlife"},
                "limit": {"type": "integer", "description": "Max results (default 10)"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "search_restaurants",
        "description": "Find restaurants and dining options in a city or neighbourhood.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City or neighbourhood"},
                "cuisine": {"type": "string", "description": "Cuisine type (optional)"},
                "price_range": {"type": "string", "description": "budget | mid-range | upscale"},
                "limit": {"type": "integer", "description": "Max results (default 6)"},
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get weather forecast for a destination during the trip dates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["city", "start_date", "end_date"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for travel info: visa requirements, transport options, local tips, best areas, safety, currency, cost of living.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
    },
]
