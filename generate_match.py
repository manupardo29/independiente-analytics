import sys

from src.metrics import calcular_metricas_partido
from src.normalize import normalizar_partido
from src.storage import cargar_json, guardar_json
from src.validation import validar_partido
from src.visualizations import (
    crear_comparacion_general,
    crear_perfil_ofensivo,
    crear_rendimiento_individual,
    crear_xi_ratings,
)

def mostrar_porcentaje(valor):
    if valor is None:
        return "N/D"

    return f"{valor}%"

def intentar_generar_placa(
    nombre,
    funcion,
    args
):
    """
    Genera UNA placa sin arriesgar el resto del batch.

    Si la funcion devuelve None (esa placa puntual no tiene
    datos suficientes para este partido - por ejemplo, sin
    alineacion no hay XI) o levanta una excepcion, se reporta
    como omitida y seguimos con las demas. La idea es que el
    programa genere todas las placas POSIBLES en cada corrida;
    la curacion de cuales publicar (y en que posteo) queda de
    tu lado, despues, mirando que se genero.
    """
    try:
        resultado = funcion(*args)

    except Exception as error:
        print(
            f"  [omitida] {nombre}: {error}"
        )
        return None

    if resultado is None:
        print(
            f"  [omitida] {nombre}: "
            f"datos insuficientes para este partido"
        )
        return None

    print(
        f"  [generada] {nombre} -> {resultado}"
    )
    return resultado

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

    ruta_ataque = (
        f"outputs/figures/"
        f"fixture_{fixture_id}_attack_profile.png"
    )

    ruta_xi = (
        f"outputs/figures/"
        f"fixture_{fixture_id}_starting_xi.png"
    )

    ruta_individual = (
        f"outputs/figures/"
        f"fixture_{fixture_id}_individual.png"
    )

    placas = [
        (
            "Comparacion general",
            crear_comparacion_general,
            (partido, ruta_figura),
        ),
        (
            "Ataque y calidad de ocasiones",
            crear_perfil_ofensivo,
            (partido, metricas, ruta_ataque),
        ),
        (
            "XI inicial y ratings",
            crear_xi_ratings,
            (partido, ruta_xi),
        ),
        (
            "Rendimiento individual",
            crear_rendimiento_individual,
            (partido, metricas, ruta_individual),
        ),
    ]

    print()
    print("Generando placas...")

    rutas_generadas = {}

    for nombre, funcion, args in placas:
        rutas_generadas[nombre] = intentar_generar_placa(
            nombre,
            funcion,
            args
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

    print()
    print("Resumen de placas:")

    for nombre, ruta in rutas_generadas.items():
        if ruta:
            print(f"  OK  {nombre} -> {ruta}")
        else:
            print(f"  --  {nombre} (omitida)")



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