"""
Configuration management for StockTracker backend.

Loads settings from config.yaml and provides a typed Settings object
for use throughout the application.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


# Resolve paths relative to the backend/ directory
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"


@dataclass
class DatabaseSettings:
    url: str = "sqlite+aiosqlite:///./stocktracker.db"


@dataclass
class SchedulerSettings:
    refresh_interval_seconds: int = 30
    market_hours_only: bool = False


@dataclass
class CorsSettings:
    origins: list[str] = field(default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])


@dataclass
class ServerSettings:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class Settings:
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    scheduler: SchedulerSettings = field(default_factory=SchedulerSettings)
    cors: CorsSettings = field(default_factory=CorsSettings)
    server: ServerSettings = field(default_factory=ServerSettings)


def load_settings(config_path: Path = CONFIG_PATH) -> Settings:
    """
    Load application settings from a YAML config file.
    Falls back to defaults if the file is missing or a section is absent.
    """
    settings = Settings()

    if not config_path.exists():
        return settings

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # Database
    db_raw = raw.get("database", {})
    if db_raw:
        settings.database = DatabaseSettings(
            url=db_raw.get("url", settings.database.url),
        )

    # Scheduler
    sched_raw = raw.get("scheduler", {})
    if sched_raw:
        settings.scheduler = SchedulerSettings(
            refresh_interval_seconds=int(
                sched_raw.get("refresh_interval_seconds",
                              settings.scheduler.refresh_interval_seconds)
            ),
            market_hours_only=bool(
                sched_raw.get("market_hours_only",
                              settings.scheduler.market_hours_only)
            ),
        )

    # CORS
    cors_raw = raw.get("cors", {})
    if cors_raw:
        settings.cors = CorsSettings(
            origins=cors_raw.get("origins", settings.cors.origins),
        )

    # Server
    server_raw = raw.get("server", {})
    if server_raw:
        settings.server = ServerSettings(
            host=server_raw.get("host", settings.server.host),
            port=int(server_raw.get("port", settings.server.port)),
        )

    return settings


# Module-level singleton — imported by other modules as `from app.config import settings`
settings = load_settings()
