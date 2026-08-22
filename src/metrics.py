def calcular_porcentaje(parte, total):
    if parte is None or total in (None, 0):
        return None

    return round(
        parte / total * 100,
        1
    )


def calcular_ratio(parte, total, decimales=3):
    if parte is None or total in (None, 0):
        return None

    return round(
        parte / total,
        decimales
    )


def calcular_metricas_equipo(
    equipo,
    goles
):
    stats = equipo["statistics"]
    tiros = stats["shots"]

    return {
        "shot_accuracy_pct": calcular_porcentaje(
            tiros["on_target"],
            tiros["total"]
        ),

        "inside_box_pct": calcular_porcentaje(
            tiros["inside_box"],
            tiros["total"]
        ),

        "goal_conversion_pct": calcular_porcentaje(
            goles,
            tiros["total"]
        ),

        "xg_per_shot": calcular_ratio(
            stats["expected_goals"],
            tiros["total"]
        ),

        "goals_minus_xg": (
            round(
                goles - stats["expected_goals"],
                2
            )
            if stats["expected_goals"] is not None
            else None
        ),
    }


def calcular_metricas_partido(partido):
    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    goles = partido["match"]["score"]

    home_metricas = calcular_metricas_equipo(
        home,
        goles["home"]
    )

    away_metricas = calcular_metricas_equipo(
        away,
        goles["away"]
    )

    home_stats = home["statistics"]
    away_stats = away["statistics"]

    tiros_totales = (
        home_stats["shots"]["total"]
        + away_stats["shots"]["total"]
    )

    xg_total = (
        home_stats["expected_goals"]
        + away_stats["expected_goals"]
    )

    home_metricas["shot_share_pct"] = (
        calcular_porcentaje(
            home_stats["shots"]["total"],
            tiros_totales
        )
    )

    away_metricas["shot_share_pct"] = (
        calcular_porcentaje(
            away_stats["shots"]["total"],
            tiros_totales
        )
    )

    home_metricas["xg_share_pct"] = (
        calcular_porcentaje(
            home_stats["expected_goals"],
            xg_total
        )
    )

    away_metricas["xg_share_pct"] = (
        calcular_porcentaje(
            away_stats["expected_goals"],
            xg_total
        )
    )

    return {
        "home": home_metricas,
        "away": away_metricas,

        "comparison": {
            "shot_difference": (
                home_stats["shots"]["total"]
                - away_stats["shots"]["total"]
            ),

            "xg_difference": round(
                home_stats["expected_goals"]
                - away_stats["expected_goals"],
                2
            ),

            "possession_difference": (
                home_stats["possession_pct"]
                - away_stats["possession_pct"]
            ),
        },
        "players": {
            "home": calcular_metricas_jugadores_equipo(
                home
            ),

            "away": calcular_metricas_jugadores_equipo(
                away
            ),
        },
    }

def calcular_metricas_jugador(jugador):
    duelos = jugador["duels"]
    regates = jugador["dribbles"]

    goles = jugador["goals"]
    asistencias = jugador["assists"]

    contribuciones_gol = (
        (goles or 0)
        + (asistencias or 0)
    )

    return {
        "id": jugador["id"],
        "name": jugador["name"],
        "minutes": jugador["minutes"],
        "rating": jugador["rating"],

        "pass_accuracy_pct": (
            jugador["passes"]["accuracy_pct"]
        ),

        "duel_win_pct": calcular_porcentaje(
            duelos["won"],
            duelos["total"]
        ),

        "dribble_success_pct": calcular_porcentaje(
            regates["successful"],
            regates["attempted"]
        ),

        "goal_contributions": contribuciones_gol,
    }


def calcular_metricas_jugadores_equipo(equipo):
    jugadores = []

    for jugador in equipo["players"]:
        if jugador["minutes"] is None:
            continue

        jugadores.append(
            calcular_metricas_jugador(
                jugador
            )
        )

    return jugadores