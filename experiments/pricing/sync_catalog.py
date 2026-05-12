import os
from dotenv import load_dotenv
from ibm_vpc import VpcV1
from ibm_platform_services import GlobalCatalogV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

load_dotenv()
api_key = os.getenv("IBMCLOUD_API_KEY")


def test_live_sync():
    print("🚀 Starting Live API Sync Test...")
    auth = IAMAuthenticator(api_key)

    vpc_service = VpcV1(authenticator=auth)
    catalog_service = GlobalCatalogV1(authenticator=auth)

    try:
        print("🔍 Fetching profile details from VPC API...")
        profiles = vpc_service.list_instance_profiles().get_result()

        test_profile = profiles['profiles'][0]
        p_name = test_profile['name']

        print(f"✅ Found Profile: {p_name}")
        print(f"💰 Pulling pricing for {p_name} from Catalog...")

        # Explicitly passing None for object_id
        pricing_data = catalog_service.list_artifacts(
            None,
            q=f"name:{p_name} active:true",
            include="metadata.pricing"
        ).get_result()

        if pricing_data.get('resources'):
            res = pricing_data['resources'][0]
            metadata = res.get('metadata', {})
            pricing = metadata.get('pricing', {})

            print(f"🌟 SUCCESS! Found live pricing artifact for {p_name}")
            print(f"Pricing Metadata Found: {True if pricing else False}")
            # If this prints, we can parse the specific metric for 'hourly'
            return True
        else:
            print(f"❌ Catalog search returned 0 results for '{p_name}'")
            return False

    except Exception as e:
        print(f"⚠️ Sync Test Failed: {e}")
        return False


if __name__ == "__main__":
    test_live_sync()
