import json
import re
import requests


def get_nearby_hotspot_cases(lat, lng):
    """Function for performing HTTP request to MySj hotspot API"""
    body = [{
        "lat": lat,
        "lng": lng,
        "classification": "LOW_RISK_NS"
    }]

    headers = {"Authorization": "Basic A2"}

    params = (('type', 'search'),)

    # POST request to MySj hotspot API
    response = requests.post(
        'https://mysejahtera.malaysia.gov.my/register/api/nearby/hotspots',
        headers=headers,
        json=body,
        params=params)

    # Retrieve msg from response
    data = json.loads(response.text)
    message = data['messages']['en_US']

    # Extract case number from msg
    result = re.search(r"been\s([0-9]+)\sreported", message)

    if(result == None):
        return 0

    return result.group(1)
