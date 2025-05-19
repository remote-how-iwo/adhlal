"""Allow asyncio on Windows when running as a module."""
import sys
import asyncio


def patch_windows_event_loop():  # noqa: D401 – imperative
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # type: ignore[attr-defined]
        except AttributeError:
            pass 