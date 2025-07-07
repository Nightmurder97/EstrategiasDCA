import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional

from .base_collector import BaseCollector
from .models import DefiLlamaProtocol, CollectedDataItem # Using models for structure

logger = logging.getLogger(__name__)

DEFILLAMA_API_BASE_URL = "https://api.llama.fi"

class DefiLlamaCollector(BaseCollector):
    """
    Collects data from DeFiLlama API.
    """

    def __init__(self):
        super().__init__() # No API key needed for public DeFiLlama endpoints

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Helper function to make asynchronous HTTP GET requests to DeFiLlama API.
        """
        url = f"{DEFILLAMA_API_BASE_URL}{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
                    logger.debug(f"Successfully fetched data from {url}. Status: {response.status}")
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"AIOHTTP client error fetching {url}: {e}")
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}")
        return None

    async def get_all_protocols(self) -> List[DefiLlamaProtocol]:
        """
        Fetches a list of all protocols from DeFiLlama.
        Endpoint: /protocols
        """
        protocols_data = await self._make_request("/protocols")
        if protocols_data and isinstance(protocols_data, list):
            protocols = []
            for p_data in protocols_data:
                try:
                    # Add 'id' if missing and 'defillamaId' exists (common in some endpoints)
                    if 'id' not in p_data and 'defillamaId' in p_data:
                        p_data['id'] = p_data['defillamaId']

                    # Ensure 'name' exists, provide a default if not
                    if 'name' not in p_data:
                        p_data['name'] = f"Unknown Protocol ({p_data.get('id', 'N/A')})"

                    protocols.append(DefiLlamaProtocol(**p_data))
                except Exception as e: # Catch Pydantic validation errors or others
                    logger.warning(f"Could not parse protocol data: {p_data}. Error: {e}")
            logger.info(f"Fetched {len(protocols)} protocols from DeFiLlama.")
            return protocols
        logger.warning("No protocol data received from DeFiLlama or data is not in list format.")
        return []

    async def get_protocol_tvl(self, protocol_slug: str) -> Optional[Dict[str, Any]]:
        """
        Fetches TVL and details for a specific protocol by its slug.
        Endpoint: /protocol/{protocol_slug}
        """
        # Slug is usually the 'slug' field from /protocols or derived from name
        # For simplicity, if the main get_all_protocols returns a 'slug' field in DefiLlamaProtocol, use that.
        # Otherwise, this method might need adjustment based on how slugs are obtained.
        data = await self._make_request(f"/protocol/{protocol_slug}")
        if data:
            logger.info(f"Fetched TVL data for protocol: {protocol_slug}")
            return data # This can be further modeled if needed
        return None

    async def get_yields(self,
                         chain: Optional[str] = None,
                         project: Optional[str] = None) -> List[Dict[str, Any]]: # Placeholder for more specific model
        """
        Fetches yield opportunities.
        Endpoint: /yields
        Can be filtered by chain or project.
        """
        params = {}
        if chain:
            params['chain'] = chain
        if project:
            params['project'] = project

        yields_data = await self._make_request("/yields", params=params)
        if yields_data and 'data' in yields_data and isinstance(yields_data['data'], list):
            # Here, you might want to parse into DefiLlamaYield model
            # For now, returning raw pool data
            logger.info(f"Fetched {len(yields_data['data'])} yield opportunities. Filters: chain={chain}, project={project}")
            return yields_data['data']
        logger.warning(f"No yield data received or in expected format. Filters: chain={chain}, project={project}")
        return []

    async def collect_data(self, *args, **kwargs) -> List[CollectedDataItem]:
        """
        Collects various data points from DeFiLlama.
        For this example, it will fetch all protocols.
        More specific collection logic can be added based on args/kwargs or separate methods.
        """
        collected_items = []

        # Example: Fetch all protocols
        protocols = await self.get_all_protocols()
        if protocols:
            for protocol in protocols:
                item = CollectedDataItem(
                    source="DeFiLlama",
                    data_type="protocol_info",
                    symbol=protocol.symbol if protocol.symbol else protocol.name, # Use name if symbol is missing
                    raw_data=protocol.dict() # Convert Pydantic model to dict
                )
                collected_items.append(item)

        # Example: Fetch yields (can be made more specific)
        # For demonstration, let's fetch top 5 pools by TVL (hypothetically)
        # The /yields endpoint returns a lot of data, so filtering/prioritization is key.
        # This is a simplified example; real implementation would need more robust handling.
        all_yields_raw = await self.get_yields()
        if all_yields_raw:
            # Sort by TVL and take top N, for example (assuming tvlUsd is present)
            # This is a placeholder for more sophisticated selection logic
            sorted_yields = sorted(all_yields_raw, key=lambda y: y.get('tvlUsd', 0), reverse=True)
            for yield_pool_data in sorted_yields[:5]: # Top 5 for example
                try:
                    # You might want to use DefiLlamaYield model here if fields are consistent
                    item = CollectedDataItem(
                        source="DeFiLlama",
                        data_type="yield_opportunity",
                        symbol=yield_pool_data.get('symbol', 'N/A'),
                        raw_data=yield_pool_data
                    )
                    collected_items.append(item)
                except Exception as e:
                    logger.warning(f"Could not process yield data: {yield_pool_data}. Error: {e}")

        logger.info(f"DefiLlamaCollector collected {len(collected_items)} items in total.")
        return collected_items


# Example of how to use the collector (for testing purposes)
async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    collector = DefiLlamaCollector()

    print("--- Fetching all protocols ---")
    protocols = await collector.get_all_protocols()
    if protocols:
        print(f"Found {len(protocols)} protocols. First 3:")
        for p in protocols[:3]:
            print(f"  Name: {p.name}, Symbol: {p.symbol}, TVL: {p.tvl}, Chain: {p.chain}") # Assumes these fields exist in model
    else:
        print("No protocols found or error fetching.")

    print("\n--- Fetching TVL for a specific protocol (e.g., 'uniswap') ---")
    # Note: 'uniswap' is a slug. If get_all_protocols doesn't return slugs, this needs adjustment.
    # For now, assuming 'uniswap' is a valid slug.
    tvl_data = await collector.get_protocol_tvl("uniswap")
    if tvl_data:
        print(f"TVL data for Uniswap (first few keys):")
        for key, value in list(tvl_data.items())[:5]: # Print first 5 key-value pairs
             print(f"  {key}: {str(value)[:100]}") # Print part of value to keep it short
    else:
        print("No TVL data found for Uniswap or error fetching.")

    print("\n--- Fetching yield opportunities (top 5 by TVL, example) ---")
    # This will use the collect_data method which includes yield fetching
    # collected_data_items = await collector.collect_data()
    # yield_items = [item for item in collected_data_items if item.data_type == "yield_opportunity"]
    # if yield_items:
    #     print(f"Found {len(yield_items)} yield opportunities. Example details:")
    #     for y_item_model in yield_items[:2]: # Print first 2
    #         y_data = y_item_model.raw_data
    #         print(f"  Project: {y_data.get('project')}, Pool: {y_data.get('poolMeta', y_data.get('pool'))}, APY: {y_data.get('apy')}% on chain {y_data.get('chain')} with TVL ${y_data.get('tvlUsd', 0):,.0f}")
    # else:
    #     print("No yield opportunities found or error fetching via collect_data.")

    # More direct test of get_yields
    print("\n--- Fetching ALL yield opportunities (raw, can be large) ---")
    raw_yields = await collector.get_yields()
    if raw_yields:
        print(f"Found {len(raw_yields)} raw yield pools. Example details of first 2:")
        for y_data in raw_yields[:2]:
             print(f"  Project: {y_data.get('project')}, Pool ID: {y_data.get('pool')}, Symbol: {y_data.get('symbol')}, APY: {y_data.get('apy')}% on chain {y_data.get('chain')} with TVL ${y_data.get('tvlUsd', 0):,.0f}")
    else:
        print("No raw yield opportunities found.")


if __name__ == "__main__":
    # This allows running `python -m src.data_market_agent.defillama_collector` from root for testing
    # Or just `python src/data_market_agent/defillama_collector.py`
    asyncio.run(main())
