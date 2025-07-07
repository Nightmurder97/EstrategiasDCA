# src/data_market_agent/__init__.py

from .base_collector import BaseCollector
from .defillama_collector import DefiLlamaCollector
from .agent_scheduler import AgentScheduler
from . import models # Make models accessible via the package, e.g., data_market_agent.models.CollectedDataItem

__all__ = [
    "BaseCollector",
    "DefiLlamaCollector",
    "AgentScheduler",
    "models",
]

# Basic logging setup for the agent module (can be configured further)
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
