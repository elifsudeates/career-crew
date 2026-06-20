import httpx


async def extract_job_from_url(url: str, api_key: str = None) -> str:
    headers = {"Accept": "text/markdown"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://r.jina.ai/{url}", headers=headers, timeout=15.0)
        r.raise_for_status()
        return r.text
