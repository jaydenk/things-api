"""Read-only access to Things 3 data via things.py."""

from __future__ import annotations

import things


class ThingsReader:
    """Wraps things.py, injecting db_path when configured."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    def _kwargs(self, **extra) -> dict:
        """Build kwargs, adding filepath if configured."""
        kw = {k: v for k, v in extra.items() if v is not None}
        if self._db_path:
            kw["filepath"] = self._db_path
        return kw

    def todos(self, **filters) -> list[dict]:
        return things.todos(**self._kwargs(**filters))

    def projects(self, **filters) -> list[dict]:
        return things.projects(**self._kwargs(**filters))

    def areas(self, include_items: bool = False) -> list[dict]:
        return things.areas(**self._kwargs(include_items=include_items))

    def tags(self, include_items: bool = False) -> list[dict]:
        return things.tags(**self._kwargs(include_items=include_items))

    def get(self, uuid: str) -> dict | None:
        return things.get(uuid, **self._kwargs())

    def search(self, query: str) -> list[dict]:
        return things.search(query, **self._kwargs())

    def inbox(self) -> list[dict]:
        return things.inbox(**self._kwargs())

    def today(self) -> list[dict]:
        return things.today(**self._kwargs())

    def upcoming(self) -> list[dict]:
        return things.upcoming(**self._kwargs())

    def anytime(self) -> list[dict]:
        return things.anytime(**self._kwargs())

    def someday(self) -> list[dict]:
        return things.someday(**self._kwargs())

    def logbook(self, **filters) -> list[dict]:
        return things.logbook(**self._kwargs(**filters))

    def completed(self, **filters) -> list[dict]:
        return things.completed(**self._kwargs(**filters))

    def canceled(self, **filters) -> list[dict]:
        return things.canceled(**self._kwargs(**filters))

    def trash(self) -> list[dict]:
        return things.trash(**self._kwargs())

    def deadlines(self) -> list[dict]:
        return things.deadlines(**self._kwargs())

    def checklist_items(self, todo_uuid: str) -> list[dict]:
        return things.checklist_items(todo_uuid, **self._kwargs())

    def tags_for_item(self, tag_title: str) -> list[dict]:
        return things.tags(title=tag_title, include_items=True, **self._kwargs())
