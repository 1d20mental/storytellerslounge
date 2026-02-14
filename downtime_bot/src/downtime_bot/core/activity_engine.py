from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

ResolverFn = Callable[[dict[str, Any], dict[str, Any]], Awaitable[dict[str, Any]]]


class ActivityEngine:
    def __init__(self):
        self._resolvers: dict[str, ResolverFn] = {}

    def register(self, activity_key: str, resolver_fn: ResolverFn) -> None:
        self._resolvers[activity_key] = resolver_fn

    async def resolve(self, activity_key: str, project: dict[str, Any], activity: dict[str, Any]) -> dict[str, Any]:
        if activity_key not in self._resolvers:
            raise ValueError(f"No resolver registered for activity key: {activity_key}")
        return await self._resolvers[activity_key](project, activity)
