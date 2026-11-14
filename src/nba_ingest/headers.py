"""Headers de dominio que stats.nba.com espera en cada petición.

User-Agent y Sec-Ch-Ua* los genera `impersonate="chrome"` (curl_cffi) para que
coincidan con la huella TLS; aquí solo van los headers funcionales. Ver
`docs/spike_endpoints.md` para la evidencia.
"""

BASE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nba.com",
    "Referer": "https://www.nba.com/",
}


def build_headers(user_agent: str | None = None) -> dict[str, str]:
    """Devuelve los headers; el User-Agent solo se envía si se sobrescribe explícitamente."""
    headers = dict(BASE_HEADERS)
    if user_agent and user_agent.strip():
        headers["User-Agent"] = user_agent.strip()
    return headers
