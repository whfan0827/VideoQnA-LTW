import requests
import os
from azure.identity import DefaultAzureCredential, ClientSecretCredential

from .consts import Consts


def get_arm_access_token(consts:Consts) -> str:
    '''
    Get an access token for the Azure Resource Manager
    使用 Service Principal 或 DefaultAzureCredential 進行認證

    :param consts: Consts object
    :return: Access token for the Azure Resource Manager
    '''
    # 優先使用 Service Principal 認證
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    
    if client_id and client_secret and tenant_id:
        print("使用 Service Principal 進行認證...")
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
    else:
        print("使用 Default Azure Credential 進行認證...")
        credential = DefaultAzureCredential()
    
    scope = f"{consts.AzureResourceManager}/.default"
    token = credential.get_token(scope)
    return token.token


def get_account_access_token_async(consts, arm_access_token, permission_type='Contributor', scope='Account',
                                   video_id=None):
    '''
    Get an access token for the Video Indexer account

    :param consts: Consts object
    :param arm_access_token: Access token for the Azure Resource Manager
    :param permission_type: Permission type for the access token
    :param scope: Scope for the access token
    :param video_id: Video ID for the access token, if scope is Video. Otherwise, not required
    :return: Access token for the Video Indexer account
    '''

    headers = {
        'Authorization': 'Bearer ' + arm_access_token,
        'Content-Type': 'application/json'
    }

    url = f'{consts.AzureResourceManager}/subscriptions/{consts.SubscriptionId}/resourceGroups/{consts.ResourceGroup}' + \
          f'/providers/Microsoft.VideoIndexer/accounts/{consts.AccountName}/generateAccessToken?api-version={consts.ApiVersion}'

    params = {
        'permissionType': permission_type,
        'scope': scope
    }

    if video_id is not None:
        params['videoId'] = video_id

    response = requests.post(url, json=params, headers=headers)

    # check if the response is valid
    response.raise_for_status()

    access_token = response.json().get('accessToken')

    return access_token
