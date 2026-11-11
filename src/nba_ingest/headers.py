"""Headers HTTP que stats.nba.com espera en cada petición.

Único sitio a tocar si la NBA cambia sus requisitos. Los valores vienen de la
versión Java anterior y aún NO están verificados: se confirman en la tarea 0
(`docs/spike_endpoints.md`) con una petición real.
"""

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

BASE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}


def build_headers(user_agent: str | None = None) -> dict[str, str]:
    """Devuelve los headers completos; sin User-Agent válido usa `DEFAULT_USER_AGENT`."""
    headers = dict(BASE_HEADERS)
    headers["User-Agent"] = user_agent.strip() if user_agent and user_agent.strip() else DEFAULT_USER_AGENT
    return headers
