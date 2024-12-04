from builtins import dict, int, max, str
from typing import List, Callable, Union, Optional, Dict
from urllib.parse import urlencode
from uuid import UUID

from fastapi import Request
from app.schemas.link_schema import Link
from app.schemas.pagination_schema import PaginationLink

# Utility function to create a link
def create_link(rel: str, href: str, method: str = "GET", action: str = None) -> Link:
    return Link(rel=rel, href=href, method=method, action=action)

def create_pagination_link(rel: str, base_url: str, params: dict) -> PaginationLink:
    # Ensure parameters are added in a specific order
    query_string = f"skip={params['skip']}&limit={params['limit']}"
    return PaginationLink(rel=rel, href=f"{base_url}?{query_string}")

def create_user_links(user_id: UUID, request) -> dict:
    base_url = "http://testserver"  # Use consistent base URL for tests
    return {
        'self': Link(rel="self", href=f"{base_url}/users/{user_id}"),
        'update': Link(rel="update", href=f"{base_url}/users/{user_id}"),
        'delete': Link(rel="delete", href=f"{base_url}/users/{user_id}")
    }

def generate_pagination_links(request, skip: int, limit: int, total_items: int, filters: dict = None) -> dict:
    base_url = "http://testserver/users"
    query_params = {
        'skip': skip,
        'limit': limit
    }
    if filters:
        query_params.update(filters)
    
    query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
    
    return {
        'self': Link(rel="self", href=f"{base_url}?{query_string}"),
        'first': Link(rel="first", href=f"{base_url}?skip=0&limit={limit}"),
        'last': Link(rel="last", href=f"{base_url}?skip={max(0, ((total_items - 1) // limit) * limit)}&limit={limit}"),
        **({"next": Link(rel="next", href=f"{base_url}?skip={skip + limit}&limit={limit}")} if skip + limit < total_items else {}),
        **({"prev": Link(rel="prev", href=f"{base_url}?skip={max(0, skip - limit)}&limit={limit}")} if skip > 0 else {})
    }

def create_verification_link(token: str) -> str:
    return f"http://testserver/verify_email?token={token}"
