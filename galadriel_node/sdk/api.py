from typing import Dict
from typing import Optional
from typing import Tuple
from urllib.parse import urlencode
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientConnectorError

from galadriel_node.sdk.entities import SdkError


async def get(
    api_url: str, endpoint: str, api_key: str, query_params: Optional[Dict] = None
) -> Tuple[int, Dict]:
    if query_params:
        encoded_params = urlencode(query_params)
        url = urljoin(api_url + "/", endpoint) + f"?{encoded_params}"
    else:
        url = urljoin(api_url + "/", endpoint)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
            ) as response:
                if response.status != 200:
                    return response.status, {}
                return response.status, await response.json()
    except ClientConnectorError as e:
        raise SdkError(f"Cannot connect to {api_url}, make sure it is correct")
    except Exception as e:
        raise SdkError(f"Failed to GET API endpoint: {endpoint}")
