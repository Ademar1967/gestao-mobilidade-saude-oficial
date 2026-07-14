import openrouteservice
from django.conf import settings


def carregar_ors_api_key():
    return getattr(settings, "ORS_API_KEY", "")


def geocode_address_ors(client, address):
    try:
        geocode = client.pelias_search(text=address)
        if not geocode["features"]:
            return None, None
        coords = geocode["features"][0]["geometry"]["coordinates"]
        return coords[0], coords[1]
    except Exception:
        return None, None


def calcular_rota_otimizada_ors(origem, destinos):
    api_key = carregar_ors_api_key()
    client = openrouteservice.Client(key=api_key)
    enderecos_viagem = [origem] + destinos
    coordenadas = []
    coordenadas_latlon = []
    for endereco in enderecos_viagem:
        lon, lat = geocode_address_ors(client, endereco)
        if None not in (lon, lat):
            coordenadas.append([lon, lat])
            coordenadas_latlon.append([lat, lon])
        else:
            return None, f"Endereço não encontrado: {endereco}"
    if len(coordenadas) < 2:
        return None, "Forneça pelo menos origem e um destino."
    jobs = [{"id": i + 1, "location": coord} for i, coord in enumerate(coordenadas[1:])]
    vehicles = [
        {
            "id": 1,
            "profile": "driving-car",
            "start": coordenadas[0],
            "end": coordenadas[0],
        }
    ]
    tsp_payload = {"jobs": jobs, "vehicles": vehicles}
    try:
        result = client.optimization(**tsp_payload)
        ordem = [step["job"] for step in result["routes"][0]["steps"] if "job" in step]
        roteiro_otimizado = [enderecos_viagem[0]] + [enderecos_viagem[i] for i in ordem]
        roteiro_coords = [coordenadas_latlon[0]] + [
            coordenadas_latlon[i] for i in ordem
        ]
        # Solicitar rota real (linha) para o trajeto otimizado
        route = client.directions(
            coordinates=[coordenadas[i] for i in ([0] + ordem)],
            profile="driving-car",
            format="geojson",
        )
        distancia = (
            route["features"][0]["properties"]["segments"][0]["distance"] / 1000
        )  # km
        duracao = (
            route["features"][0]["properties"]["segments"][0]["duration"] / 60
        )  # minutos
        return {
            "roteiro": roteiro_otimizado,
            "coordenadas": roteiro_coords,
            "distancia_km": distancia,
            "duracao_min": duracao,
            "geojson": route,
        }, None
    except Exception as e:
        return None, str(e)
