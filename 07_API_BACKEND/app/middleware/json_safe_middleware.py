from __future__ import annotations

import json
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from app.utils.json_safe import sanitize_for_json


class JsonSafeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Don't touch streaming or non-json responses
        if isinstance(response, StreamingResponse):
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        try:
            # read body (may be bytes)
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk

            if not body_bytes:
                return response

            text = body_bytes.decode(response.charset or "utf-8")
            data = json.loads(text)
            safe = sanitize_for_json(data)
            new_body = json.dumps(safe, ensure_ascii=False).encode("utf-8")

            headers = dict(response.headers)
            headers["content-length"] = str(len(new_body))

            return Response(content=new_body, status_code=response.status_code, headers=headers, media_type="application/json")
        except Exception:
            # If anything goes wrong, return original response
            return response
