import logging
import logging.config
from pathlib import Path
from typing import Optional
from config.settings import settings


def setup_logging():
    """Setup logging configuration for the application"""

    # Create logs directory if it doesn't exist
    if settings.LOG_FILE:
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': settings.LOG_FORMAT
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': settings.LOG_LEVEL,
                'class': 'logging.StreamHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            'layerx': {
                'level': settings.LOG_LEVEL,
                'handlers': ['console'],
                'propagate': False
            },
            'layerx.execution': {
                'level': settings.LOG_LEVEL,
                'handlers': ['console'],
                'propagate': False
            },
        },
        'root': {
            'level': logging.WARNING,
            'handlers': ['console']
        }
    }

    # Add file handler if LOG_FILE is configured
    if settings.LOG_FILE:
        logging_config['handlers']['file'] = {
            'level': settings.LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': settings.LOG_FILE,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        }
        # Add file handler to loggers
        for logger_name in ['layerx', 'layerx.execution']:
            logging_config['loggers'][logger_name]['handlers'].append('file')

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with proper naming convention"""
    return logging.getLogger(f"layerx.{name}")


def log_request_data(logger: logging.Logger, endpoint: str, **kwargs):
    """Log request data in a structured format"""
    log_data = {
        'endpoint': endpoint,
        'timestamp': None,  # Will be added by logger
    }
    log_data.update(kwargs)

    # Filter out sensitive information
    safe_data = {k: v for k, v in log_data.items() if not _is_sensitive_field(k)}

    logger.info(f"REQUEST_DATA: {safe_data}")


def log_execution_step(logger: logging.Logger, execution_id: str, step_name: str, **kwargs):
    """Log execution step with contextual data"""
    log_data = {
        'execution_id': execution_id,
        'step': step_name,
    }
    log_data.update(kwargs)

    # Filter out sensitive information
    safe_data = {k: v for k, v in log_data.items() if not _is_sensitive_field(k)}

    logger.info(f"EXECUTION_STEP: {safe_data}")


def _is_sensitive_field(field_name: str) -> bool:
    """Check if field contains sensitive information"""
    sensitive_fields = {
        'password', 'token', 'key', 'secret', 'credential',
        'openai_api_key', 'auth', 'authorization'
    }
    return field_name.lower() in sensitive_fields or any(
        sensitive in field_name.lower() for sensitive in sensitive_fields
    )