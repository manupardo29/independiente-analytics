import sys

from src.metrics import calcular_metricas_partido
from src.normalize import normalizar_partido
from src.storage import cargar_json, guardar_json
from src.validation import validar_partido
from src.visualizations import (
    crear_comparacion_general,
    crear_perfil_ofensivo,
    crear_xi_ratings,
)

def mostrar_porcentaje(valor):
    if valor is None:
        return "N/D"

    return f"{valor}%"

def generar_partido(fixture_id):
    ruta_raw = (
        f"data/raw/fixture_{fixture_id}.json"
    )

    ruta_normalized = (
        f"data/normalized/fixture_{fixture_id}.json"
    )

    print(
        f"Cargando fixture {fixture_id}..."
    )

    partido_raw = cargar_json(
        ruta_raw
    )

    print(
        "Validando datos..."
    )

    validacion = validar_partido(
        partido_raw
    )

    if not validacion["valid"]:
        print()
        print(
            "No se puede generar el partido."
        )
        print(
            "Se detectaron problemas:"
        )

        for problema in validacion["issues"]:
            print(
                "-",
                problema
            )

        return

    print(
        "Datos validos."
    )

    print(
        "Normalizando partido..."
    )

    partido = normalizar_partido(
        partido_raw
    )

    print(
        "Calculando metricas..."
    )

    metricas = calcular_metricas_partido(
        partido
    )

    guardar_json(
        partido,
        ruta_normalized
    )

    ruta_figura = (
        f"outputs/figures/"
        f"fixture_{fixture_id}_team_comparison.png"
    )

    crear_comparacion_general(
        partido,
        ruta_figura
    )

    ruta_ataque = (
        f"outputs/figures/"
        f"fixture_{fixture_id}_attack_profile.png"
    )

    crear_perfil_ofensivo(
        partido,
        metricas,
        ruta_ataque
    )

    ruta_xi = (
        f"outputs/figures/"
        f"fixture_{fixture_id}_starting_xi.png"
    )

    crear_xi_ratings(
        partido,
        ruta_xi
    )

    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    score = partido["match"]["score"]

    print()
    print("=" * 60)

    print(
        f"{home['name']} "
        f"{score['home']} - "
        f"{score['away']} "
        f"{away['name']}"
    )

    print("=" * 60)

    for lado in ["home", "away"]:
        equipo = partido["teams"][lado]
        datos = metricas[lado]

        print()
        print(equipo["name"])

        print(
            "Precision de tiro:",
            datos["shot_accuracy_pct"],
            "%"
        )

        print(
            "Tiros dentro del area:",
            datos["inside_box_pct"],
            "%"
        )

        print(
            "Conversion de gol:",
            datos["goal_conversion_pct"],
            "%"
        )

        print(
            "xG por tiro:",
            datos["xg_per_shot"]
        )
        print(
            "Participacion en tiros:",
            datos["shot_share_pct"],
            "%"
        )
        print(
            "Participacion en xG:",
            datos["xg_share_pct"],
            "%"
        )
        print(
            "Goles - xG:",
            datos["goals_minus_xg"]
        )

    comparacion = metricas["comparison"]

    print()
    print("Comparacion del partido")

    print(
    "Diferencia de tiros:",
    comparacion["shot_difference"]
    )

    print(
    "Diferencia de xG:",
    comparacion["xg_difference"]
    )

    print(
    "Diferencia de posesion:",
    comparacion["possession_difference"],
    "p.p."
    )

    print()
    print("=" * 60)
    print("TOP JUGADORES POR RATING")
    print("=" * 60)


    for lado in ["home", "away"]:
        equipo = partido["teams"][lado]

        jugadores = metricas[
            "players"
        ][lado]

        jugadores_con_rating = [
            jugador
            for jugador in jugadores
            if jugador["rating"] is not None
        ]

        jugadores_ordenados = sorted(
            jugadores_con_rating,
            key=lambda jugador: jugador["rating"],
            reverse=True
        )

        print()
        print(equipo["name"])

        for jugador in jugadores_ordenados[:5]:
            print(
                jugador["name"],
                "| rating:",
                jugador["rating"],
                "| pases:",
                mostrar_porcentaje(
                    jugador["pass_accuracy_pct"]
                ),
                "| duelos:",
                mostrar_porcentaje(
                    jugador["duel_win_pct"]
                ),
                "| regates:",
                mostrar_porcentaje(
                    jugador["dribble_success_pct"]
                ),
                "| G+A:",
                jugador["goal_contributions"],
            )                       

    print()
    print(
        f"Partido normalizado guardado en: "
        f"{ruta_normalized}"
    )
    print(
        f"Grafico guardado en: "
        f"{ruta_figura}"
    )

    print(
        f"Grafico ofensivo guardado en: "
        f"{ruta_ataque}"
    )

    print(
        f"Grafico XI guardado en: "
        f"{ruta_xi}"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Uso: python generate_match.py <fixture_id>"
        )
        sys.exit(1)

    try:
        fixture_id = int(
            sys.argv[1]
        )

    except ValueError:
        print(
            "El fixture_id debe ser un numero entero."
        )
        sys.exit(1)

    generar_partido(
        fixture_id
    )