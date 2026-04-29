import os
from dotenv import load_dotenv
from ibm_vpc import VpcV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_platform_services.global_search_v2 import GlobalSearchV2

# 1. Load credentials from .env
load_dotenv()
api_key = os.getenv("IBMCLOUD_API_KEY")


def fetch_vpc_profiles(region_name="us-south"):
    """Connects to IBM Cloud and retrieves VSI profiles for a region."""
    try:
        authenticator = IAMAuthenticator(api_key)
        service = VpcV1(authenticator=authenticator)

        base_url = f"https://{region_name}.iaas.cloud.ibm.com/v1"
        service.set_service_url(base_url)

        print(f"--- Fetching VSI Profiles for {region_name} ---")

        profiles = service.list_instance_profiles().get_result()

        for profile in profiles['profiles'][:5]:
            name = profile['name']
            vcpus = profile['vcpu_count']['value']
            ram = profile['memory']['value']
            print(f"Profile: {name} | vCPUs: {vcpus} | RAM: {ram}GB")

        return True

    except Exception as e:
        print(f"Error connecting to IBM Cloud: {e}")
        return False


def get_profile_price(profile_name):
    """
    Uses Global Search V2 to find the pricing artifact.
    This avoids the 'object_id' requirement of the Catalog service.
    """
    try:
        auth = IAMAuthenticator(api_key)
        search_service = GlobalSearchV2(authenticator=auth)

        # Broken into multiple lines for PEP 8 E501 compliance
        query_str = f"name:{profile_name} AND kind:pricing"

        search_result = search_service.search(
            query=query_str,
            fields=["*"]
        ).get_result()

        if search_result.get('items'):
            item = search_result['items'][0]
            artifact_id = item.get('id')
            print(f"💰 Success! Found pricing ID for {profile_name}")
            print(f"ID: {artifact_id}")
            return artifact_id

        print(f"❌ Could not find search results for {profile_name}")
        return None

    except Exception as e:
        print(f"Search failed for {profile_name}: {e}")
        return None


if __name__ == "__main__":
    if not api_key:
        print("Error: No API Key found in .env file!")
    else:
        if fetch_vpc_profiles():
            get_profile_price("bx2-2x8")
