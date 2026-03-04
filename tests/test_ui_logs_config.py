import importlib.util
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "services" / "ui_logs_config.py"
    spec = importlib.util.spec_from_file_location("ui_logs_config", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load ui_logs_config module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_ui_logs_config_defaults_when_missing():
    parse_ui_logs_config = _load_module().parse_ui_logs_config
    cfg = parse_ui_logs_config({})
    assert cfg.poll_interval_seconds == 3
    assert cfg.max_events_per_poll == 200


def test_parse_ui_logs_config_clamps_values():
    parse_ui_logs_config = _load_module().parse_ui_logs_config
    cfg = parse_ui_logs_config(
        {
            "ui": {
                "logs": {
                    "poll_interval_seconds": 0,
                    "max_events_per_poll": 9999,
                }
            }
        }
    )
    assert cfg.poll_interval_seconds == 1
    assert cfg.max_events_per_poll == 500
