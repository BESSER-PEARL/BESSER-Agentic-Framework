import atexit
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine

from baf.core.property import Property
from baf.db import DB_MONITORING_DIALECT, DB_MONITORING_HOST, DB_MONITORING_PORT, DB_MONITORING_DATABASE, \
    DB_MONITORING_USERNAME, DB_MONITORING_PASSWORD
from baf.db.monitoring_db import MonitoringDB
from baf.exceptions.logger import logger


def _flatten_yaml_properties(data: Any, config: dict[str, Any], prefix: str = '') -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            next_prefix = f'{prefix}.{key}' if prefix else str(key)
            _flatten_yaml_properties(value, config, next_prefix)
        return

    if isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, dict) and len(item) == 1:
                item_key, item_value = next(iter(item.items()))
                next_prefix = f'{prefix}.{item_key}' if prefix else str(item_key)
                _flatten_yaml_properties(item_value, config, next_prefix)
            else:
                next_prefix = f'{prefix}.{index}' if prefix else str(index)
                _flatten_yaml_properties(item, config, next_prefix)
        return

    if prefix:
        config[prefix] = data


def load_properties(path: str) -> dict[str, Any] | None:
    config: dict[str, Any] = {}
    suffix = Path(path).suffix.lower()

    if suffix not in {'.yaml', '.yml'}:
        logger.error('Only YAML config files are supported (.yaml, .yml): %s', path)
        return None

    with open(path, encoding='utf-8') as config_file:
        loaded_config = yaml.safe_load(config_file) or {}
    if not isinstance(loaded_config, dict):
        logger.error('YAML config must contain a mapping at root level: %s', path)
        return None

    _flatten_yaml_properties(loaded_config, config)
    return config


def _coerce_property_value(value: Any, target_type: type) -> Any:
    if isinstance(value, target_type):
        return value

    if target_type is bool:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {'true', '1', 'yes', 'y', 'on'}:
                return True
            if normalized in {'false', '0', 'no', 'n', 'off'}:
                return False
            raise ValueError(f'Cannot parse boolean value from {value!r}')
        if isinstance(value, (int, float)):
            return bool(value)

    if target_type in {str, int, float}:
        return target_type(value)

    return value


def get_property(config: dict[str, Any], prop: Property) -> Any:
    value = config.get(prop.name)

    if value is None:
        return prop.default_value

    try:
        return _coerce_property_value(value, prop.type)
    except (TypeError, ValueError):
        logger.warning(
            "Could not cast property '%s' value %r to %s. Using default value %r",
            prop.name,
            value,
            prop.type,
            prop.default_value,
        )
        return prop.default_value


def close_connection(monitoring_db: MonitoringDB):
    logger.info('Closing DB connection...')
    if monitoring_db is not None:
        monitoring_db.close_connection()


def connect_to_db(config_path: str):
    # Path to the configuration file where the DB credentials are defined
    config = load_properties(config_path)
    if config is not None:
        monitoring_db = MonitoringDB()
        try:
            dialect = get_property(config, DB_MONITORING_DIALECT)
            host = get_property(config, DB_MONITORING_HOST)
            port = get_property(config, DB_MONITORING_PORT)
            database = get_property(config, DB_MONITORING_DATABASE)
            username = get_property(config, DB_MONITORING_USERNAME)
            password = get_property(config, DB_MONITORING_PASSWORD)
            url = f"{dialect}://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(url)
            monitoring_db.conn = engine.connect()
            atexit.register(close_connection, monitoring_db)
            logger.info('Connected to DB')
            return monitoring_db
        except Exception as e:
            logger.error("An error occurred while trying to connect to the monitoring DB in the monitoring UI. "
                         "See the attached exception:")
            logger.error(e)
            return None
    else:
        logger.error(f"The file {config_path} could not be read")
