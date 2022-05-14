import requests
import pandas as pd
import os
import logging
import yaml
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant_id", nargs=1, required=True)
    parser.add_argument("--config", nargs=1)
    parser.add_argument("--files", nargs=1)
    parser.add_argument("--folder", nargs=1, default="")
    parser.add_argument("--separator", nargs=1, default=",")
    return parser.parse_args()


def get_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    This function takes in client id and client secrets as argments and returns an authentication token that can be used to call the Power BI Rest API.

    Parameters
    ----------
    tenant_id : str
         Tenant ID is a globally unique identifier (GUID) that is different than your organization name or domain.
    client_id : str
         The client ID and secret is unique to the client application on that authorization server.
    client_secret : str
         The client ID and secret is unique to the client application on that authorization server.

    Returns
    -------
    access_token : str
        Authentication token to use when calling the Power BI Rest API.

    """
    url = "https://login.microsoftonline.com/" + tenant_id + "/oauth2/token"

    payload = {
        'grant_type': 'client_credentials',
        'scope': 'oauth',
        'resource': 'https://analysis.windows.net/powerbi/api',
        'client_id': client_id,
        'client_secret': client_secret,
        'response_mode': 'query'}

    logging.info("Requesting access token")
    response = requests.request("GET", url, data=payload)
    logging.info(f'Response {response}')
    logging.info(f"Access Token {response.json().get('access_token')}")
    return f"Bearer  {response.json().get('access_token')}"


def get_workspace_id(access_token: str, workspace_name: str) -> str:
    """
     This function takes in access token, and workspace name as argments
     and returns the workspace id of that workspace name.

     Parameters
     ----------
     access_token : str
           The access_token is used to make rest api calls to the Power BI Rest API.
     workspace_name : str
          Unique name for a workspace
    """
    logging.info(f"Getting workspace id for dataset:{workspace_name}")
    headers = {'Authorization': access_token}
    url = f"https://api.powerbi.com/v1.0/myorg/groups?$filter=contains(name,'{workspace_name}')"
    response = requests.request("GET", url, headers=headers)
    workspaces = pd.DataFrame(response.json().get('value'))
    workspace_id = workspaces[workspaces.name == workspace_name]["id"].iloc[0]

    logging.info(f"Workspace Id for {workspace_name} = {workspace_id}")
    return workspace_id


def get_datasets_in_workspace(access_token: str, workspace_id: str):
    """
     This function takes in access token and workspace id as argments and returns a list of datasets in that workspace.

     Parameters
     ----------
     access_token : str
           The access_token is used to make rest api calls to the Power BI Rest API.
     workspace_id : str
          Unique id for a workspace
    """

    headers = {'Authorization': access_token}
    logging.info(f"Requesting list of datasets for workspace:{workspace_id}")

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"

    response = requests.request("GET", url, headers=headers)
    datasets = pd.DataFrame(response.json().get('value'))

    return datasets


def get_dataset_id(access_token: str, workspace_id: str, dataset_name: str) -> str:
    """
     This function takes in access token, workspace id and dataset name as argments
     and returns the dataset id of that workspace.

     Parameters
     ----------
     access_token : str
           The access_token is used to make rest api calls to the Power BI Rest API.
     workspace_id : str
          Unique id for a workspace
     dataset_name: str
          Name of the dataset
    """
    logging.info(f"Getting dataset id for dataset:{dataset_name}")
    datasets = get_datasets_in_workspace(access_token=access_token,
                                         workspace_id=workspace_id)

    dataset_id = datasets[datasets.name == dataset_name]["id"].iloc[0]

    logging.info(f"Dataset Id for {dataset_name}:{dataset_id}")
    return dataset_id


def assign_group_principal(access_token: str, workspace_name: str, dataset_name: str, identifier: str, permission: str):
    """
     This function takes in access token, workspace id, dataset name, and permission requirements
     as argments and assigns a user to the specified dataset.

     Parameters
     ----------
     access_token : str
           The access_token is used to make rest api calls to the Power BI Rest API.
     workspace_name : str
          Unique name for a workspace
     dataset_name: str
          Name of the dataset
     identifier: str
          Unique identifies for Azure AD Group
     permission: str
          The access right that the user has for the dataset (permission level)
    """

    headers = {'Authorization': access_token}

    workspace_id = get_workspace_id(access_token=access_token,
                                    workspace_name=workspace_name)

    dataset_id = get_dataset_id(access_token=access_token,
                                workspace_id=workspace_id,
                                dataset_name=dataset_name)

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/users"
    body = {
        'identifier': identifier,
        'principalType': 'Group',
        'datasetUserAccessRight': permission
    }
    response = requests.request("POST", url, headers=headers, data=body)
    logging.info(
        f"Identifier Id({identifier}) assigned {permission} permission to  {workspace_name}")


def find_updated_datasets(file_list, folder, cfg):
    updated_datasets = {}

    parsed_file_list = []

    for file in file_list:
        path = Path(file)

        # Ignore deleted files
        if os.path.exists(file) and len(path.parts) != 0 and file.endswith(".json") and not file.startswith("."):
            if folder:
                if file.startswith(folder):
                    parsed_file_list.append(file[len(folder):])
            else:
                parsed_file_list.append(file)

    for file in parsed_file_list:
        path = Path(file)
        # If we have a config, create a map from dataset to folder
        if cfg:
            dataset = path.parts[1]
            if not dataset.startswith(".") and dataset not in updated_datasets:
                updated_datasets[dataset] = path.parts[0]
        # If we don't have a config, leave the mapping blank
        else:
            dataset = path.parts[0]
            if not dataset.startswith(".") and dataset not in updated_datasets:
                updated_datasets[dataset] = ""

    return updated_datasets


def main():
    args = parse_arguments()
    tenant_id = args.tenant_id[0]
    config = args.config[0] if args.config else None
    files = args.files[0]
    file_list = files.split(args.separator)
    folder = args.folder[0] if args.folder else ""
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']

    if client_id is None or client_secret is None:
        raise Exception(
            "CLIENT_ID and CLIENT_SECRET environment variables must be set with credentials")

    if config is None:
        raise Exception("Requires either a config file")
    else:
        with open(config, 'r') as yml_file:
            cfg = yaml.safe_load(yml_file)

    # Add values for client_id, client_secret and tenant_id below
    access_token = get_access_token(tenant_id=tenant_id,
                                    client_id=client_id,
                                    client_secret=client_secret)

    updated_datasets = find_updated_datasets(file_list, folder, cfg)

    for dataset, workspace_name in updated_datasets.items():
        group_permissions = cfg["Dataset Permissions"][workspace_name]["group_permissions"]
        print(group_permissions)
        for permission, identifiers in group_permissions.items():
            for indentifier in identifiers:
                assign_group_principal(access_token=access_token,
                                       workspace_name=workspace_name,
                                       dataset_name=dataset,
                                       identifier=indentifier,
                                       permission=permission)


if __name__ == '__main__':
    main()
