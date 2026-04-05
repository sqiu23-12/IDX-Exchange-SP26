import csv
import requests
from datetime import datetime, timedelta
import pandas as pd
import glob

# API setup
base_url = 'https://api-trestle.corelogic.com/trestle/odata/Property'
auth_endpoint = 'https://idxexchange.com/internal-api/trestle_token.php?key=IDXEXCHANGE2026_CHANGE_THIS'

response = requests.get(auth_endpoint, timeout=30)
response.raise_for_status()
token = response.json().get('access_token')

headers = {'Authorization': f'Bearer {token}'}

# Date range
start_date = datetime(2024, 1, 1)
end_date = datetime(2026, 4, 1)
current = start_date

# LOOP THROUGH MONTHS
while current < end_date:
    next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)

    print(f"Processing listings: {current.strftime('%Y-%m')}")

    url = base_url
    params = {
        '$select': 'ListingKey,UnparsedAddress,City,PostalCode,PropertyType,LivingArea,ListPrice,BedroomsTotal,BathroomsTotalInteger,ListingContractDate',
        '$filter': f"ListingContractDate ge {current.isoformat(timespec='milliseconds')}Z and ListingContractDate lt {next_month.isoformat(timespec='milliseconds')}Z",
        '$top': 1000
    }

    csv_file = f"CRMLSListing{current.strftime('%Y%m')}.csv"

    with open(csv_file, mode='w', newline='') as file:
        writer = None

        while True:
            response = requests.get(url, params=params, headers=headers)
            data = response.json()
            observations = data.get('value', [])

            if not observations:
                break

            if writer is None:
                writer = csv.DictWriter(file, fieldnames=observations[0].keys())
                writer.writeheader()

            for obs in observations:
                writer.writerow(obs)

            if '@odata.nextLink' in data:
                url = data['@odata.nextLink']
                params = None
            else:
                break

    current = next_month

# COMBINE ALL FILES
files = glob.glob("CRMLSListing*.csv")
df = pd.concat([pd.read_csv(f) for f in files])
df.to_csv("combined_listings.csv", index=False)

print("Listings complete ✅")