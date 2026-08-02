import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from .models import Paciente

geolocator = Nominatim(user_agent="gestao_mobilidade_saude")


def geocodificar_paciente(paciente):
    endereco = f"{paciente.rua or ''}, {paciente.bairro or ''}, {paciente.cidade or ''}, {paciente.cep or ''}, Brasil"

    for tentativa in range(3):
        try:
            location = geolocator.geocode(endereco, timeout=10)
            if location:
                paciente.latitude = location.latitude
                paciente.longitude = location.longitude
                paciente.save(update_fields=["latitude", "longitude"])
                return True
            return False
        except (GeocoderTimedOut, GeocoderServiceError):
            time.sleep(2)
    return False


def geocodificar_pendentes():
    pendentes = Paciente.objects.filter(latitude__isnull=True)
    total = pendentes.count()
    sucesso = 0

    for i, p in enumerate(pendentes, 1):
        if geocodificar_paciente(p):
            sucesso += 1
        time.sleep(1.1)
        if i % 50 == 0:
            print(f"Progresso: {i}/{total} | Sucesso: {sucesso}")

    print(f"✅ Pronto! {sucesso}/{total} geocodificados com sucesso.")
    return sucesso
