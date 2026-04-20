import openrouteservice
from django.conf import settings

def carregar_ors_api_key():
    return getattr(settings, 'ORS_API_KEY', '')

def geocode_address(address):
    api_key = carregar_ors_api_key()
    client = openrouteservice.Client(key=api_key)
    try:
        geocode = client.pelias_search(text=address)
        if not geocode['features']:
            return None
        coords = geocode['features'][0]['geometry']['coordinates']
        return {'longitude': coords[0], 'latitude': coords[1]}
    except Exception:
        return None
