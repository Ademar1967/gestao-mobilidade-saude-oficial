import pandas as pd
import random


def gerar_pacientes(turno: str, n: int = 20):
    nomes = [f"Paciente {i + 1}" for i in range(n)]
    enderecos = [f"Rua Exemplo, {100 + i}" for i in range(n)]
    bairros = ["Centro", "Vila Industrial", "Jardim Armênia", "Socorro"] * (n // 4 + 1)
    horarios = (
        [f"{8 + i // 2:02d}:{30 if i % 2 else 0:02d}" for i in range(n)]
        if turno == "diurno"
        else [f"{18 + i // 2:02d}:{30 if i % 2 else 0:02d}" for i in range(n)]
    )
    destinos = ["Hospital das Clínicas", "Instituto do Coração"] * (n // 2)
    enfermagem = [random.choice([True, False]) for _ in range(n)]
    return pd.DataFrame(
        {
            "nome": nomes,
            "endereco": enderecos,
            "bairro": bairros[:n],
            "cidade": ["Mogi das Cruzes"] * n,
            "horario_consulta": horarios,
            "destino": destinos[:n],
            "necessita_enfermagem": enfermagem,
        }
    )


def gerar_veiculos(n_amb: int = 5, n_van: int = 3):
    ambs = [
        {
            "tipo": "Ambulância",
            "patrimonio": f"11{79 + i}",
            "placa": f"ABC{i}D23",
            "r1": True,
            "capacidade": 2,
            "condutor": f"Condutor {i + 1}",
            "enfermagem_nome": f"Enf. {i + 1}",
            "enfermagem_graduacao": random.choice(["Enfermeiro", "Técnico"]),
        }
        for i in range(n_amb)
    ]
    vans = [
        {
            "tipo": "Van",
            "patrimonio": f"VAN{i + 1}",
            "placa": f"HIJ{i}K89",
            "r1": False,
            "capacidade": 4,
            "condutor": f"Condutor V{i + 1}",
            "enfermagem_nome": None,
            "enfermagem_graduacao": None,
        }
        for i in range(n_van)
    ]
    return pd.DataFrame(ambs + vans)
