import requests

payload = {
    "customer_id": "CUST1007",
    "password": "Kavya@123",
    "location": "North Sentinel Island"
}

resp = requests.post("http://127.0.0.1:8001/api/v1/customer/login", json=payload)
print(resp.status_code)
print(resp.json())
