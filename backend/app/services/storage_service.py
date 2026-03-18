import uuid

import httpx

from app.core.config import settings


async def upload_markdown(content: str, module_id: uuid.UUID) -> str:
    """
    Uploads a Markdown string to the Supabase 'modules' storage bucket.
    Uses upsert so re-exporting the same module overwrites the existing file.
    Returns the public download URL.
    """
    bucket = "modules"
    path = f"{module_id}.md"
    upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{path}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            upload_url,
            content=content.encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "text/markdown",
                "x-upsert": "true",
            },
        )
        response.raise_for_status()

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
    return public_url
