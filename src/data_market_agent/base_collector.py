from abc import ABC, abstractmethod
from typing import List, Any, Dict
import logging

logger = logging.getLogger(__name__)

class BaseCollector(ABC):
    """
    Abstract base class for data collectors.
    Each collector will fetch data from a specific source.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    @abstractmethod
    async def collect_data(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Collects data from the source.
        Should be implemented by subclasses.
        Returns a list of data items (dictionaries).
        """
        pass

    def process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes the raw data.
        Default implementation returns data as is.
        Subclasses can override this for specific processing.
        """
        logger.debug(f"Processing data in {self.__class__.__name__} (default implementation).")
        return raw_data

    async def fetch_and_process(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches raw data and then processes it.
        """
        logger.info(f"Fetching data using {self.__class__.__name__}...")
        raw_data = await self.collect_data(*args, **kwargs)
        if raw_data:
            logger.info(f"Successfully fetched {len(raw_data)} items using {self.__class__.__name__}.")
            processed_data = self.process_data(raw_data)
            logger.info(f"Processed {len(processed_data)} items using {self.__class__.__name__}.")
            return processed_data
        logger.warning(f"No data fetched by {self.__class__.__name__}.")
        return []

    def get_source_name(self) -> str:
        """
        Returns the name of the data source.
        By default, it's the class name minus "Collector".
        """
        name = self.__class__.__name__
        if name.endswith("Collector"):
            return name[:-9]
        return name
