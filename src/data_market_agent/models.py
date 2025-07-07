from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import datetime

class CollectedDataItem(BaseModel):
    """
    A Pydantic model for a single piece of data collected by a collector.
    """
    source: str = Field(..., description="Name of the data source (e.g., 'DeFiLlama', 'Binance')")
    data_type: str = Field(..., description="Type of data (e.g., 'tvl', 'protocol_yield', 'market_price')")
    symbol: Optional[str] = Field(None, description="Asset symbol or identifier, if applicable (e.g., 'BTC', 'Uniswap')")
    timestamp_utc: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, description="Timestamp of when the data was collected or is valid for (UTC)")
    raw_data: Dict[str, Any] = Field(..., description="The actual data payload from the source")

    # Optional metadata fields
    processed_data: Optional[Dict[str, Any]] = Field(None, description="Processed or transformed version of the data")
    collection_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata about the collection process itself")

    class Config:
        # Example for how to generate schema examples
        # schema_extra = {
        #     "example": {
        #         "source": "DeFiLlama",
        #         "data_type": "protocol_tvl",
        #         "symbol": "Uniswap",
        #         "timestamp_utc": "2023-10-26T10:00:00Z",
        #         "raw_data": {"tvl": 1000000000, "chain": "Ethereum"},
        #     }
        # }
        validate_assignment = True # Ensure fields are validated on assignment after instantiation
        frozen = False # Allow modification after creation if needed, though generally aim for immutability for collected items.
                       # Can be set to True if items should be strictly immutable.

class DefiLlamaProtocol(BaseModel):
    """
    Represents a DeFi protocol from DeFiLlama.
    Adjust fields based on actual API response from DeFiLlama.
    """
    id: str
    name: str
    symbol: Optional[str] = None
    chain: Optional[str] = None # This might be 'chains' as a list in actual data
    tvl: Optional[float] = None
    # Add other relevant fields from DeFiLlama's API like category, chains, etc.
    # Example: category: Optional[str] = None
    # Example: chains: Optional[List[str]] = []

    class Config:
        extra = 'ignore' # Ignore extra fields from API response not defined in model

class DefiLlamaYield(BaseModel):
    """
    Represents yield data for a pool/protocol from DeFiLlama.
    Adjust fields based on actual API response.
    """
    pool: str # Pool ID or identifier
    project: str # Project name
    chain: str
    symbol: str
    tvlUsd: float
    apy: Optional[float] = None
    apyBase: Optional[float] = None
    apyReward: Optional[float] = None
    # Add other relevant fields like ilRisk, poolMeta, etc.

    class Config:
        extra = 'ignore'

# Update __init__.py for models
# This is not a file creation, but a mental note to update it if I were managing many models.
# For now, BaseCollector and AgentScheduler are the main structural components.
# The models.py file itself is self-contained for now.
