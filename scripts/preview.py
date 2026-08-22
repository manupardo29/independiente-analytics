"""
Scratchpad para iterar rapido sobre las visualizaciones.

Antes esto se hacia copiando todo visualizations.py dentro de
test.py y tocando ese duplicado. El problema: las dos copias
terminan divergiendo (nos paso con el fix del offset de
xytext, que quedo aplicado en visualizations.py pero no en
test.py). Este script no duplica nada - importa las funciones
reales, asi que siempre esta probando el mismo codigo que
corre generate_match.py.

Uso:
    python scripts/preview.py <fixture_id>

Requiere que ya exista data/normalized/fixture_<id>.json
(corre generate_match.py primero si todavia no lo generaste).
"""
import sys

from src.metrics import calcular_metricas_partido
from src.storage import cargar_json
from src.visualizations import (
    crear_comparacion_general,
    crear_perfil_ofensivo,
    crear_xi_ratings,
)


def preview(fixture_id):
    ruta_normalized = (
        f"data/normalized/fixture_{fixture_id}.json"
    )

    partido = cargar_json(ruta_normalized)

    metricas = calcular_metricas_partido(partido)

    crear_comparacion_general(
        partido,
        f"outputs/figures/fixture_{fixture_id}_team_comparison.png",
    )

    crear_perfil_ofensivo(
        partido,
        metricas,
        f"outputs/figures/fixture_{fixture_id}_attack_profile.png",
    )

    crear_xi_ratings(
        partido,
        f"outputs/figures/fixture_{fixture_id}_starting_xi.png",
    )

    print(
        f"Placas regeneradas para el fixture {fixture_id} "
        f"en outputs/figures/"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/preview.py <fixture_id>")
        sys.exit(1)

    preview(int(sys.argv[1]))
