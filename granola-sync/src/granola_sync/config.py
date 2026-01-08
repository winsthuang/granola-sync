"""Configuration management for granola-sync."""
import json
from pathlib import Path
from typing import Optional, Dict, Any

CONFIG_DIR = Path.home() / ".granola-sync"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}

    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(config: Dict[str, Any]):
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_api_url() -> Optional[str]:
    """Get the configured API URL."""
    config = load_config()
    return config.get('api_url')


def set_api_url(url: str):
    """Set the API URL."""
    config = load_config()
    config['api_url'] = url.rstrip('/')
    save_config(config)


def get_api_key() -> Optional[str]:
    """Get the configured API key."""
    config = load_config()
    return config.get('api_key')


def set_api_key(key: str):
    """Set the API key."""
    config = load_config()
    config['api_key'] = key
    save_config(config)


def get_user_info() -> Optional[Dict[str, Any]]:
    """Get stored user info from cloud login."""
    config = load_config()
    return config.get('user_info')


def set_user_info(info: Dict[str, Any]):
    """Store user info from cloud login."""
    config = load_config()
    config['user_info'] = info
    save_config(config)


def is_logged_in() -> bool:
    """Check if user is logged into the cloud API."""
    return bool(get_api_key() and get_api_url())


def clear_config():
    """Clear all configuration."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
