import requests

_API_BASE = "https://slack.com/api"


class SlackAPIError(Exception):
    pass


def get(token: str, method: str, params: dict | None = None) -> dict:
    r = requests.get(
        f"{_API_BASE}/{method}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise SlackAPIError(f"{method}: {data.get('error', 'unknown')} | response={data}")
    return dict(data)


def post(token: str, method: str, payload: dict) -> dict:
    r = requests.post(
        f"{_API_BASE}/{method}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("ok"):
        raise SlackAPIError(f"{method}: {data.get('error', 'unknown')} | response={data}")
    return dict(data)
