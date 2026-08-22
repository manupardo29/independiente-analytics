import os

import requests
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.getenv(
    "API_FOOTBALL_BASE_URL",
    "https://v3.football.api-sports.io"
)

API_KEY = os.getenv("API_FOOTBALL_KEY")


def hacer_peticion(endpoint, params=None):
    if not API_KEY:
        raise RuntimeError(
            "No se encontro API_FOOTBALL_KEY en el archivo .env"
        )

    respuesta = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers={
            "x-apisports-key": API_KEY
        },
        params=params,
        timeout=30
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    if datos["errors"]:
        raise RuntimeError(
            f"API-Football devolvio errores: {datos['errors']}"
        )

    return datos


def obtener_fixture(fixture_id):
    datos = hacer_peticion(
        "fixtures",
        {
            "id": fixture_id
        }
    )

    if datos["results"] == 0:
        raise ValueError(
            f"No se encontro el fixture {fixture_id}"
        )

    return datos["response"][0]

def buscar_equipo(nombre):
    datos = hacer_peticion(
        "teams",
        {
            "search": nombre
        }
    )

    return datos["response"]

def obtener_partidos_equipo(team_id, desde, hasta):
    datos = hacer_peticion(
        "fixtures",
        {
            "team": team_id,
            "from": desde,
            "to": hasta
        }
    )

    return datos["response"]

def obtener_partidos_equipo_fecha(team_id, fecha, temporada):
    datos = hacer_peticion(
        "fixtures",
        {
            "team": team_id,
            "season": temporada,
            "date": fecha
        }
    )

    return datos["response"]

def obtener_partidos_fecha(fecha):
    datos = hacer_peticion(
        "fixtures",
        {
            "date": fecha
        }
    )

    return datos["response"]

def obtener_estadisticas_fixture(fixture_id):
    datos = hacer_peticion(
        "fixtures/statistics",
        {
            "fixture": fixture_id
        }
    )

    return datos["response"]