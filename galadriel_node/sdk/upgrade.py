from http import HTTPStatus

from galadriel_node.sdk import api


async def version_aware_get(api_url, endpoint, api_key, query_params=None):
    status, response = await api.get(api_url, endpoint, api_key, query_params)

    if status == HTTPStatus.UPGRADE_REQUIRED:
        print(
            "Error: Your CLI version is outdated. "
            "Please update to the latest version by using 'node upgrade'. "
            "You can also find it at https://pypi.org/project/galadriel-node/"
        )

    return status, response
