import csv
import requests
from datetime import datetime, timedelta
import pandas as pd
import glob

# API setup
base_url = "https://api-trestle.corelogic.com/trestle/odata/Property"
auth_endpoint = "https://idxexchange.com/internal-api/trestle_token.php?key=IDXEXCHANGE2026_CHANGE_THIS"

response = requests.get(auth_endpoint, timeout=30)
response.raise_for_status()
token = response.json().get("access_token")

headers = {"Authorization": f"Bearer {token}"}

selected_fields = [
    "ListingKey",
    "City",
    "PostalCode",
    "ListPrice",
    "OriginalListPrice",
    "ClosePrice",
    "CloseDate",
    "ListingContractDate",
    "PurchaseContractDate",
    "LivingArea",
    "BedroomsTotal"
]

# Date range
start_date = datetime(2024, 1, 1)
end_date = datetime(2026, 4, 1)
current = start_date

while current < end_date:
    next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)

    print(f"Processing sold: {current.strftime('%Y-%m')}")

    url = base_url
    params = {
        "$select": ",".join(selected_fields),
        "$filter": (
            f"MlsStatus eq 'Closed' and "
            f"CloseDate ge {current.isoformat(timespec='milliseconds')}Z and "
            f"CloseDate lt {next_month.isoformat(timespec='milliseconds')}Z"
        ),
        "$top": 1000
    }

    csv_file = f"CRMLSSold{current.strftime('%Y%m')}.csv"

    with open(csv_file, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=selected_fields)
        writer.writeheader()

        while True:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            observations = data.get("value", [])

            if not observations:
                break

            for obs in observations:
                row = {field: obs.get(field, None) for field in selected_fields}
                writer.writerow(row)

            next_link = data.get("@odata.nextLink")

            if next_link:
                url = next_link
                params = None
            else:
                break

    current = next_month

# Combine all sold files
files = sorted(glob.glob("CRMLSSold*.csv"))

df = pd.concat([pd.read_csv(file) for file in files], ignore_index=True)

df.to_csv("combined_sold.csv", index=False)

print("Sold complete ✅")
print("Combined sold columns:")
print(df.columns)