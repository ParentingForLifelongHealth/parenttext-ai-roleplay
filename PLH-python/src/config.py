import yaml
from pathlib import Path


class ConfigValidationError(Exception):
    """Custom exception for config validation errors"""

    pass


class Config:
    """Singleton class for loading and accessing the config file"""

    _instance = None
    _config = None

    REQUIRED_FIELDS = {
        "models": ["child", "facilitator"],
        "scenario": ["name", "description", "objectives"],
        "system_prompts": [
            "child",
            "facilitator_decision",
            "facilitator_positive_reinforcement",
            "facilitator_help",
            "facilitator_summary",
        ],
        "static_messages": [
            "retry_message",
            "facilitator",
            "child",
            "summary",
            "scenario",
            "positive_question",
            "negative_question",
        ],
    }

    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._load_config(config_path)
        return cls._instance

    @classmethod
    def _load_config(cls, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as file:
                cls._config = yaml.safe_load(file)
                if cls._config is None:
                    raise ConfigValidationError("Config file is empty")
                cls._validate_config()
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML format: {str(e)}")
        except Exception as e:
            raise ConfigValidationError(f"Error loading config: {str(e)}")

    @classmethod
    def _validate_config(cls):
        """Validate that all required fields are present in the config"""
        if not isinstance(cls._config, dict):
            raise ConfigValidationError("Config must be a dictionary")

        missing_fields = []

        for section, fields in cls.REQUIRED_FIELDS.items():
            if section not in cls._config:
                missing_fields.append(f"Missing section: {section}")
                continue

            if not isinstance(cls._config[section], dict):
                missing_fields.append(f"Section {section} must be a dictionary")
                continue

            for field in fields:
                if field not in cls._config[section]:
                    missing_fields.append(f"Missing field: {section}.{field}")
                elif (
                    cls._config[section][field] is None
                    or cls._config[section][field] == ""
                ):
                    missing_fields.append(f"Empty field: {section}.{field}")

        if missing_fields:
            raise ConfigValidationError(
                "Config validation failed:\n" + "\n".join(missing_fields)
            )

    @classmethod
    def get(cls, *keys, default=None):
        if cls._config is None:
            cls._load_config()

        current = cls._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
