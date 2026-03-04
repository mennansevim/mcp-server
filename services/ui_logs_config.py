from dataclasses import dataclass


@dataclass(frozen=True)
class UILogsConfig:
    poll_interval_seconds: int = 3
    max_events_per_poll: int = 200


def parse_ui_logs_config(config: dict) -> UILogsConfig:
    ui_cfg = config.get("ui") or {}
    logs_cfg = ui_cfg.get("logs") or {}

    interval = int(logs_cfg.get("poll_interval_seconds", 3))
    max_events = int(logs_cfg.get("max_events_per_poll", 200))

    return UILogsConfig(
        poll_interval_seconds=max(1, min(interval, 30)),
        max_events_per_poll=max(20, min(max_events, 500)),
    )
