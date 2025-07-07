import asyncio
import pytest
from unittest.mock import patch, AsyncMock
import aiohttp # Import for ClientResponseError

from src.data_market_agent.defillama_collector import DefiLlamaCollector
from src.data_market_agent.models import DefiLlamaProtocol, CollectedDataItem

MOCK_PROTOCOL_LIST_SUCCESS = [
    {"id": "1", "name": "Protocol One", "symbol": "PONE", "tvl": 1000000, "chain": "Ethereum"},
    {"id": "2", "name": "Protocol Two", "symbol": "PTWO", "tvl": 2000000, "chain": "Solana", "category": "Dexes"},
    {"id": "3", "name": "Protocol Three Missing Symbol", "tvl": 500000, "chain": "Ethereum"},
    {"defillamaId": "4", "name": "Protocol Four DefiId", "symbol": "PFOUR", "tvl": 700000}
]
MOCK_PROTOCOL_TVL_SUCCESS = {"id": "1", "name": "Protocol One", "symbol": "PONE", "tvl": 1200000, "chains": ["Ethereum"]}
MOCK_YIELDS_SUCCESS = {
    "status": "success",
    "data": [
        {"pool": "pool1-id", "project": "Project Alpha", "chain": "Ethereum", "symbol": "ALP-ETH", "tvlUsd": 500000, "apy": 10.5},
        {"pool": "pool2-id", "project": "Project Beta", "chain": "Solana", "symbol": "BET-SOL", "tvlUsd": 750000, "apy": 12.3}
    ]
}

@pytest.fixture
def collector():
    return DefiLlamaCollector()

def create_mock_session_manager(json_return_value=None, status_code=200, raise_for_status_error=None):
    mock_response_obj = AsyncMock(spec=aiohttp.ClientResponse)
    mock_response_obj.status = status_code
    mock_response_obj.json = AsyncMock(return_value=json_return_value)
    if raise_for_status_error:
        mock_response_obj.raise_for_status = AsyncMock(side_effect=raise_for_status_error)
    else:
        mock_response_obj.raise_for_status = AsyncMock()

    mock_response_context_mgr = AsyncMock()
    # Configure __aenter__ and __aexit__ to be AsyncMocks that return the correct values
    aenter_response_mock = AsyncMock(return_value=mock_response_obj)
    aexit_response_mock = AsyncMock(return_value=None)
    mock_response_context_mgr.__aenter__ = aenter_response_mock
    mock_response_context_mgr.__aexit__ = aexit_response_mock

    mock_session_get_method = AsyncMock(return_value=mock_response_context_mgr)

    mock_session_instance = AsyncMock(spec=aiohttp.ClientSession)
    mock_session_instance.get = mock_session_get_method
    # Configure __aenter__ and __aexit__ for the session instance itself
    aenter_session_mock = AsyncMock(return_value=mock_session_instance)
    aexit_session_mock = AsyncMock(return_value=None)
    mock_session_instance.__aenter__ = aenter_session_mock
    mock_session_instance.__aexit__ = aexit_session_mock

    return mock_session_instance

@pytest.mark.asyncio
async def test_get_all_protocols_success(collector: DefiLlamaCollector):
    mock_session = create_mock_session_manager(json_return_value=MOCK_PROTOCOL_LIST_SUCCESS)
    with patch('aiohttp.ClientSession', return_value=mock_session):
        protocols = await collector.get_all_protocols()
    assert len(protocols) == 4
    assert protocols[0].name == "Protocol One"
    mock_session.get.assert_called_once_with("https://api.llama.fi/protocols", params=None, timeout=30)

@pytest.mark.asyncio
async def test_get_all_protocols_api_error(collector: DefiLlamaCollector):
    error = aiohttp.ClientResponseError(AsyncMock(), (), status=500, message="Server Error")
    mock_session = create_mock_session_manager(raise_for_status_error=error)
    with patch('aiohttp.ClientSession', return_value=mock_session):
        protocols = await collector.get_all_protocols()
    assert len(protocols) == 0

@pytest.mark.asyncio
async def test_get_protocol_tvl_success(collector: DefiLlamaCollector):
    mock_session = create_mock_session_manager(json_return_value=MOCK_PROTOCOL_TVL_SUCCESS)
    with patch('aiohttp.ClientSession', return_value=mock_session):
        tvl_data = await collector.get_protocol_tvl("protocol-one")
    assert tvl_data["name"] == "Protocol One"
    mock_session.get.assert_called_once_with("https://api.llama.fi/protocol/protocol-one", params=None, timeout=30)

@pytest.mark.asyncio
async def test_get_yields_success(collector: DefiLlamaCollector):
    mock_session = create_mock_session_manager(json_return_value=MOCK_YIELDS_SUCCESS)
    with patch('aiohttp.ClientSession', return_value=mock_session):
        yields = await collector.get_yields()
    assert len(yields) == 2
    mock_session.get.assert_called_once_with("https://api.llama.fi/yields", params={}, timeout=30)

@pytest.mark.asyncio
async def test_get_yields_with_filters(collector: DefiLlamaCollector):
    mock_session = create_mock_session_manager(json_return_value=MOCK_YIELDS_SUCCESS)
    with patch('aiohttp.ClientSession', return_value=mock_session):
        await collector.get_yields(chain="Ethereum", project="Project Alpha")
    mock_session.get.assert_called_once_with(
        "https://api.llama.fi/yields", params={"chain": "Ethereum", "project": "Project Alpha"}, timeout=30
    )

@pytest.mark.asyncio
async def test_collect_data_integration(collector: DefiLlamaCollector):
    mock_protocols_actual_response = AsyncMock(spec=aiohttp.ClientResponse)
    mock_protocols_actual_response.status = 200
    mock_protocols_actual_response.json = AsyncMock(return_value=MOCK_PROTOCOL_LIST_SUCCESS)
    mock_protocols_actual_response.raise_for_status = AsyncMock()

    mock_protocols_context_manager = AsyncMock()
    mock_protocols_context_manager.__aenter__ = AsyncMock(return_value=mock_protocols_actual_response)
    mock_protocols_context_manager.__aexit__ = AsyncMock(return_value=None)

    mock_yields_actual_response = AsyncMock(spec=aiohttp.ClientResponse)
    mock_yields_actual_response.status = 200
    mock_yields_actual_response.json = AsyncMock(return_value=MOCK_YIELDS_SUCCESS)
    mock_yields_actual_response.raise_for_status = AsyncMock()

    mock_yields_context_manager = AsyncMock()
    mock_yields_context_manager.__aenter__ = AsyncMock(return_value=mock_yields_actual_response)
    mock_yields_context_manager.__aexit__ = AsyncMock(return_value=None)

    async def side_effect_get(url, params=None, timeout=None):
        if "protocols" in url: return mock_protocols_context_manager
        if "yields" in url: return mock_yields_context_manager
        raise ValueError(f"Unexpected URL: {url}")

    mock_session_get_method = AsyncMock(side_effect=side_effect_get)

    mock_client_session_instance = AsyncMock(spec=aiohttp.ClientSession)
    mock_client_session_instance.get = mock_session_get_method
    mock_client_session_instance.__aenter__ = AsyncMock(return_value=mock_client_session_instance)
    mock_client_session_instance.__aexit__ = AsyncMock(return_value=None)

    with patch('aiohttp.ClientSession', return_value=mock_client_session_instance):
        collected_items = await collector.collect_data()

    assert len(collected_items) == 6
    protocol_items = [item for item in collected_items if item.data_type == "protocol_info"]
    yield_items = [item for item in collected_items if item.data_type == "yield_opportunity"]
    assert len(protocol_items) == 4
    assert len(yield_items) == 2
    assert mock_client_session_instance.get.call_count == 2
pass
