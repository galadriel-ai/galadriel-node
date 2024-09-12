import importlib
from typing import Dict
from typing import Optional
from typing import Tuple
from urllib.parse import urlencode
from urllib.parse import urljoin
from http import HTTPStatus

import aiohttp
from aiohttp import ClientConnectorError

from galadriel_node.sdk.entities import SdkError

CLIENT_NAME = "gpu-node"
CLIENT_VERSION = importlib.metadata.version("galadriel-node")


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
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "client_name": CLIENT_NAME,
                    "client_version": CLIENT_VERSION,
                },
            ) as response:
                if response.status in [HTTPStatus.OK, HTTPStatus.UPGRADE_REQUIRED]:
                    return response.status, await response.json()

                return response.status, {}
    except ClientConnectorError:
        raise SdkError(f"Cannot connect to {api_url}, make sure it is correct")
    except Exception:
        raise SdkError(f"Failed to GET API endpoint: {endpoint}")
