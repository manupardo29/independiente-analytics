from pathlib import Path

import matplotlib.pyplot as plt

from mplsoccer import VerticalPitch

from matplotlib.patches import FancyBboxPatch, Rectangle

from src.theme import (
    ACCENT,
    BACKGROUND,
    DIVIDER,
    MUTED_TEXT,
    PANEL,
    RATING_AVERAGE,
    RATING_BAD,
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_NA,
    RATING_TEXT_DARK,
    RATING_TEXT_LIGHT,
    SECONDARY,
    TEXT,
    TRACK,
    aplicar_tema,
)

from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

INDEPENDIENTE_ID = 453

def obtener_colores_equipos(home, away):
    if home["id"] == INDEPENDIENTE_ID:
        return ACCENT, SECONDARY

    if away["id"] == INDEPENDIENTE_ID:
        return SECONDARY, ACCENT

    # Fallback para fixtures de desarrollo
    return ACCENT, SECONDARY

def obtener_equipo_destacado(
    partido
):
    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    if home["id"] == INDEPENDIENTE_ID:
        return home

    if away["id"] == INDEPENDIENTE_ID:
        return away

    # Fallback para fixtures de desarrollo
    return home

def buscar_datos_jugador(
    equipo,
    player_id
):
    for jugador in equipo["players"]:
        if jugador["id"] == player_id:
            return jugador

    return None

def obtener_estilo_rating(rating):
    if rating is None:
        return RATING_NA, RATING_TEXT_LIGHT

    if rating < 6.0:
        return RATING_BAD, RATING_TEXT_LIGHT

    if rating < 7.0:
        return RATING_AVERAGE, RATING_TEXT_DARK

    if rating < 8.0:
        return RATING_GOOD, RATING_TEXT_LIGHT

    return RATING_EXCELLENT, RATING_TEXT_LIGHT

def acortar_nombre(nombre):
    if not nombre:
        return "N/D"

    partes = nombre.split()

    if len(partes) == 1:
        return partes[0]

    nombre_corto = (
        f"{partes[0][0]}. "
        f"{partes[-1]}"
    )

    if len(nombre_corto) <= 15:
        return nombre_corto

    return partes[-1]

def obtener_posiciones_alineacion(
    start_xi
):
    jugadores_validos = [
        jugador
        for jugador in start_xi
        if jugador.get("grid")
    ]

    if not jugadores_validos:
        return []

    max_fila = max(
        jugador["grid"]["row"]
        for jugador in jugadores_validos
    )

    posiciones = []

    for jugador in jugadores_validos:
        fila = jugador["grid"]["row"]
        columna = jugador["grid"]["column"]

        jugadores_fila = [
            otro
            for otro in jugadores_validos
            if otro["grid"]["row"] == fila
        ]

        cantidad_fila = len(
            jugadores_fila
        )

        # Profundidad:
        # arquero cerca de x=8,
        # delanteros cerca de x=108.
        if max_fila == 1:
            x = 60
        else:
            x_min = 14
            x_max = 106

            x = (
                x_min
                + (
                    (fila - 1)
                    / (max_fila - 1)
                )
                * (x_max - x_min)
            )

        # Ancho de cancha
        y = (
            80
            * columna
            / (cantidad_fila + 1)
        )

        posiciones.append(
            {
                "player": jugador,
                "x": x,
                "y": y,
            }
        )

    return posiciones

def formatear_valor(valor, tipo):
    if valor is None:
        return "N/D"

    if tipo == "int":
        return str(int(valor))

    if tipo == "pct":
        return f"{valor:.0f}%"

    if tipo == "decimal":
        return f"{valor:.2f}"

    return str(valor)

def formatear_decimal(
    valor,
    decimales
):
    if valor is None:
        return "N/D"

    return f"{valor:.{decimales}f}"

def dibujar_barra_comparacion(
    ax,
    y,
    valor_home,
    valor_away,
    color_home,
    color_away,
    altura=0.22
):
    radio_maximo = 0.07

    # Pista completa de fondo
    pista = FancyBboxPatch(
        (-1, y - altura / 2),
        2,
        altura,
        boxstyle=(
            f"round,pad=0,"
            f"rounding_size={radio_maximo}"
        ),
        facecolor=TRACK,
        edgecolor="none",
        zorder=1,
    )

    ax.add_patch(
        pista
    )

    # Barra local
    if valor_home > 0:
        radio_home = min(
            radio_maximo,
            valor_home / 2,
            altura / 2,
        )

        barra_home = FancyBboxPatch(
            (
                -valor_home,
                y - altura / 2
            ),
            valor_home,
            altura,
            boxstyle=(
                f"round,pad=0,"
                f"rounding_size={radio_home}"
            ),
            facecolor=color_home,
            edgecolor="none",
            zorder=2,
        )

        ax.add_patch(
            barra_home
        )

        ancho_centro_home = min(
            0.08,
            valor_home / 2
        )

        centro_home = Rectangle(
            (
                -ancho_centro_home,
                y - altura / 2
            ),
            ancho_centro_home,
            altura,
            facecolor=color_home,
            edgecolor="none",
            zorder=3,
        )

        ax.add_patch(
            centro_home
        )

    # Barra visitante
    if valor_away > 0:
        radio_away = min(
            radio_maximo,
            valor_away / 2,
            altura / 2,
        )

        barra_away = FancyBboxPatch(
            (
                0,
                y - altura / 2
            ),
            valor_away,
            altura,
            boxstyle=(
                f"round,pad=0,"
                f"rounding_size={radio_away}"
            ),
            facecolor=color_away,
            edgecolor="none",
            zorder=2,
        )

        ax.add_patch(
            barra_away
        )

        ancho_centro_away = min(
            0.08,
            valor_away / 2
        )

        centro_away = Rectangle(
            (
                0,
                y - altura / 2
            ),
            ancho_centro_away,
            altura,
            facecolor=color_away,
            edgecolor="none",
            zorder=3,
        )

        ax.add_patch(
            centro_away
        )

def dibujar_tarjeta_metrica(
    ax,
    x,
    y,
    ancho,
    alto,
    etiqueta,
    valor_home,
    valor_away,
    color_home,
    color_away,
):
    tarjeta = FancyBboxPatch(
        (
            x - ancho / 2,
            y - alto / 2
        ),
        ancho,
        alto,
        boxstyle=(
            "round,pad=0,"
            "rounding_size=0.06"
        ),
        facecolor=PANEL,
        edgecolor="none",
        zorder=1,
    )

    ax.add_patch(
        tarjeta
    )

    ax.text(
        x,
        y + 0.17,
        etiqueta,
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color=MUTED_TEXT,
        zorder=2,
    )

    ax.text(
        x - ancho * 0.23,
        y - 0.10,
        valor_home,
        ha="center",
        va="center",
        fontsize=23,
        fontweight="bold",
        color=color_home,
        zorder=2,
    )

    ax.text(
        x,
        y - 0.10,
        "|",
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
        alpha=0.35,
        zorder=2,
    )

    ax.text(
        x + ancho * 0.23,
        y - 0.10,
        valor_away,
        ha="center",
        va="center",
        fontsize=23,
        fontweight="bold",
        color=color_away,
        zorder=2,
    )

def crear_comparacion_general(
    partido,
    ruta_salida
):
    aplicar_tema()

    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    color_home, color_away = obtener_colores_equipos(
        home,
        away
    )

    home_stats = home["statistics"]
    away_stats = away["statistics"]

    score = partido["match"]["score"]

    competencia = partido[
        "match"
    ]["competition"]

    estadisticas = [
        (
            "POSESION",
            home_stats["possession_pct"],
            away_stats["possession_pct"],
            "pct",
        ),
        (
            "TIROS",
            home_stats["shots"]["total"],
            away_stats["shots"]["total"],
            "int",
        ),
        (
            "TIROS AL ARCO",
            home_stats["shots"]["on_target"],
            away_stats["shots"]["on_target"],
            "int",
        ),
        (
            "xG",
            home_stats["expected_goals"],
            away_stats["expected_goals"],
            "decimal",
        ),
        (
            "PASES",
            home_stats["passes"]["total"],
            away_stats["passes"]["total"],
            "int",
        ),
        (
            "PRECISION DE PASE",
            home_stats["passes"]["accuracy_pct"],
            away_stats["passes"]["accuracy_pct"],
            "pct",
        ),
    ]

    fig, ax = plt.subplots(
        figsize=(10.8, 13.5),
        dpi=100
    )

    fig.subplots_adjust(
        left=0.06,
        right=0.94,
        top=0.95,
        bottom=0.06
    )

    logo = Image.open(
    "assets/independiente_logo.png"
    )

    imagen_logo = OffsetImage(
        logo,
        zoom=0.68,
        alpha=0.025
    )

    watermark = AnnotationBbox(
        imagen_logo,
        (0, 2.5),
        frameon=False,
        zorder=0
    )

    ax.add_artist(
        watermark
    )

    fig.patch.set_facecolor(
        BACKGROUND
    )

    ax.set_facecolor(
        BACKGROUND
    )

    cantidad = len(
        estadisticas
    )

    ax.set_xlim(
        -1.22,
        1.22
    )

    ax.set_ylim(
        -0.35,
        cantidad + 1.3
    )

    ax.axis("off")

    # Encabezado

    ax.text(
        -1.02,
        cantidad + 0.9,
        home["name"],
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if home["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        1.02,
        cantidad + 0.9,
        away["name"],
        ha="right",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if away["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        0,
        cantidad + 0.9,
        (
            f"{score['home']} "
            f"- "
            f"{score['away']}"
        ),
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=TEXT,
    )

    ax.text(
        0,
        cantidad + 0.45,
        (
            f"{competencia['name']} "
            f"| {competencia['round']}"
        ),
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
    )

    ax.plot(
        [-0.18, 0.18],
        [cantidad + 0.22, cantidad + 0.22],
        color=ACCENT,
        linewidth=3,
        solid_capstyle="round",
        zorder=4,
    )

    # Estadisticas

    for indice, estadistica in enumerate(
        estadisticas
    ):
        (
            nombre,
            valor_home,
            valor_away,
            tipo,
        ) = estadistica

        y = cantidad - 1 - indice

        home_num = (
            float(valor_home)
            if valor_home is not None
            else 0
        )

        away_num = (
            float(valor_away)
            if valor_away is not None
            else 0
        )

        if tipo == "pct":
            home_bar = home_num / 100
            away_bar = away_num / 100

        else:
            total = home_num + away_num

            if total > 0:
                home_bar = home_num / total
                away_bar = away_num / total
            else:
                home_bar = 0
                away_bar = 0

        dibujar_barra_comparacion(
            ax,
            y,
            home_bar,
            away_bar,
            color_home,
            color_away,
            altura=0.28,
        )

        ax.text(
            0,
            y + 0.29,
            nombre,
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color=MUTED_TEXT,
        )

        ax.text(
            -1.07,
            y,
            formatear_valor(
                valor_home,
                tipo
            ),
            ha="right",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=TEXT,
        )

        ax.text(
            1.07,
            y,
            formatear_valor(
                valor_away,
                tipo
            ),
            ha="left",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=TEXT,
        )


    ruta = Path(
        ruta_salida
    )

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.savefig(
        ruta,
        dpi=100,
        facecolor=BACKGROUND,
    )

    plt.close(
        fig
    )

    return ruta

def crear_perfil_ofensivo(
    partido,
    metricas,
    ruta_salida
):
    aplicar_tema()

    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    color_home, color_away = obtener_colores_equipos(
        home,
        away
    )

    home_stats = home["statistics"]
    away_stats = away["statistics"]

    home_metricas = metricas["home"]
    away_metricas = metricas["away"]

    score = partido["match"]["score"]

    competencia = partido[
        "match"
    ]["competition"]

    fig, ax = plt.subplots(
        figsize=(10.8, 13.5),
        dpi=100
    )

    fig.subplots_adjust(
        left=0.06,
        right=0.94,
        top=0.95,
        bottom=0.06
    )

    fig.patch.set_facecolor(
        BACKGROUND
    )

    ax.set_facecolor(
        BACKGROUND
    )

    ax.set_xlim(
        -1.22,
        1.22
    )

    ax.set_ylim(
        -0.35,
        7.3
    )

    ax.axis("off")

    logo = Image.open(
        "assets/independiente_logo.png"
    )

    imagen_logo = OffsetImage(
        logo,
        zoom=0.68,
        alpha=0.025
    )

    watermark = AnnotationBbox(
        imagen_logo,
        (0, 2.45),
        frameon=False,
        zorder=0
    )

    ax.add_artist(
        watermark
    )

    ax.text(
        -1.02,
        6.9,
        home["name"],
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if home["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        1.02,
        6.9,
        away["name"],
        ha="right",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if away["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax.text(
        0,
        6.9,
        (
            f"{score['home']} "
            f"- "
            f"{score['away']}"
        ),
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=TEXT,
    )

    ax.text(
        0,
        6.45,
        (
            f"{competencia['name']} "
            f"| {competencia['round']}"
        ),
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
    )

    ax.plot(
        [-0.18, 0.18],
        [6.22, 6.22],
        color=ACCENT,
        linewidth=3,
        solid_capstyle="round",
        zorder=4,
    )

    ax.text(
        0,
        5.65,
        "ATAQUE Y CALIDAD DE OCASIONES",
        ha="center",
        va="center",
        fontsize=19,
        fontweight="bold",
        color=TEXT,
    )

    dibujar_tarjeta_metrica(
        ax,
        x=-0.76,
        y=4.85,
        ancho=0.66,
        alto=0.72,
        etiqueta="TIROS",
        valor_home=str(
            home_stats["shots"]["total"]
        ),
        valor_away=str(
            away_stats["shots"]["total"]
        ),
        color_home=color_home,
        color_away=color_away,
    )

    dibujar_tarjeta_metrica(
        ax,
        x=0,
        y=4.85,
        ancho=0.66,
        alto=0.72,
        etiqueta="xG",
        valor_home=formatear_decimal(
            home_stats["expected_goals"],
            2
        ),
        valor_away=formatear_decimal(
            away_stats["expected_goals"],
            2
        ),
        color_home=color_home,
        color_away=color_away,
    )

    dibujar_tarjeta_metrica(
        ax,
        x=0.76,
        y=4.85,
        ancho=0.66,
        alto=0.72,
        etiqueta="xG POR TIRO",
        valor_home=formatear_decimal(
            home_metricas["xg_per_shot"],
            2
        ),
        valor_away=formatear_decimal(
            away_metricas["xg_per_shot"],
            2
        ),
        color_home=color_home,
        color_away=color_away,
    )

    estadisticas_pct = [
        (
            "TIROS DENTRO DEL AREA",
            home_metricas["inside_box_pct"],
            away_metricas["inside_box_pct"],
        ),
        (
            "PRECISION DE TIRO",
            home_metricas["shot_accuracy_pct"],
            away_metricas["shot_accuracy_pct"],
        ),
        (
            "CONVERSION DE GOL",
            home_metricas["goal_conversion_pct"],
            away_metricas["goal_conversion_pct"],
        ),
    ]

    posiciones_y = [
        3.65,
        2.55,
        1.45,
    ]

    for (
        nombre,
        valor_home,
        valor_away
    ), y in zip(
        estadisticas_pct,
        posiciones_y
    ):
        home_bar = (
            valor_home / 100
            if valor_home is not None
            else 0
        )

        away_bar = (
            valor_away / 100
            if valor_away is not None
            else 0
        )

        dibujar_barra_comparacion(
            ax,
            y,
            home_bar,
            away_bar,
            color_home,
            color_away,
            altura=0.28,
        )

        ax.text(
            0,
            y + 0.31,
            nombre,
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color=MUTED_TEXT,
        )

        ax.text(
            -1.07,
            y,
            (
                f"{valor_home:.1f}%"
                if valor_home is not None
                else "N/D"
            ),
            ha="right",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=TEXT,
        )

        ax.text(
            1.07,
            y,
            (
                f"{valor_away:.1f}%"
                if valor_away is not None
                else "N/D"
            ),
            ha="left",
            va="center",
            fontsize=18,
            fontweight="bold",
            color=TEXT,
        )

    ruta = Path(
        ruta_salida
    )
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.savefig(
        ruta,
        dpi=100,
        facecolor=BACKGROUND,
    )

    plt.close(
        fig
    )

    return ruta

def crear_xi_ratings(
    partido,
    ruta_salida
):
    aplicar_tema()

    home = partido["teams"]["home"]
    away = partido["teams"]["away"]

    equipo = obtener_equipo_destacado(
        partido
    )

    alineacion = equipo.get(
        "lineup"
    )

    if not alineacion:
        return None

    titulares = alineacion.get(
        "start_xi",
        []
    )

    posiciones = obtener_posiciones_alineacion(
        titulares
    )

    if not posiciones:
        return None

    score = partido["match"]["score"]

    competencia = partido[
        "match"
    ]["competition"]

    formacion = alineacion.get(
        "formation"
    )

    entrenador = alineacion.get(
        "coach",
        {}
    )

    fig = plt.figure(
        figsize=(10.8, 13.5),
        dpi=100,
        facecolor=BACKGROUND,
    )

    # Encabezado
    ax_header = fig.add_axes(
        [0.06, 0.76, 0.88, 0.19]
    )

    ax_header.set_facecolor(
        BACKGROUND
    )

    ax_header.set_xlim(
        -1.22,
        1.22
    )

    ax_header.set_ylim(
        0,
        1
    )

    ax_header.axis(
        "off"
    )

    ax_header.text(
        -1.02,
        0.82,
        home["name"],
        ha="left",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if home["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax_header.text(
        1.02,
        0.82,
        away["name"],
        ha="right",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=(
            ACCENT
            if away["id"] == INDEPENDIENTE_ID
            else TEXT
        ),
    )

    ax_header.text(
        0,
        0.82,
        (
            f"{score['home']} "
            f"- "
            f"{score['away']}"
        ),
        ha="center",
        va="center",
        fontsize=34,
        fontweight="bold",
        color=TEXT,
    )

    ax_header.text(
        0,
        0.55,
        (
            f"{competencia['name']} "
            f"| {competencia['round']}"
        ),
        ha="center",
        va="center",
        fontsize=16,
        color=MUTED_TEXT,
    )

    ax_header.plot(
        [-0.18, 0.18],
        [0.40, 0.40],
        color=ACCENT,
        linewidth=3,
        solid_capstyle="round",
    )

    ax_header.text(
        0,
        0.15,
        "XI INICIAL Y RATINGS",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color=TEXT,
    )

    fig.text(
        0.5,
        0.745,
        (
            f"{equipo['name']}  |  "
            f"{formacion}  |  "
            f"DT: {entrenador.get('name', 'N/D')}"
        ),
        ha="center",
        va="center",
        fontsize=14,
        color=MUTED_TEXT,
    )

    ax_pitch = fig.add_axes(
        [0.12, 0.07, 0.76, 0.64]
    )

    pitch = VerticalPitch(
        pitch_type="statsbomb",
        pitch_color=PANEL,
        line_color=DIVIDER,
        linewidth=1.5,
        corner_arcs=True,
        goal_type="box",
    )

    pitch.draw(
        ax=ax_pitch
    )

    for posicion in posiciones:
        jugador_lineup = posicion[
            "player"
        ]

        x = posicion["x"]
        y = posicion["y"]

        datos = buscar_datos_jugador(
            equipo,
            jugador_lineup["id"]
        )

        rating = (
            datos["rating"]
            if datos
            else None
        )

        numero = jugador_lineup.get(
            "number"
        )

        nombre = acortar_nombre(
            jugador_lineup.get(
                "name"
            )
        )

        color_rating, color_texto_rating = (
            obtener_estilo_rating(
                rating
            )
        )

        # Circulo del jugador
        pitch.scatter(
            x,
            y,
            s=1050,
            color=TRACK,
            edgecolors=ACCENT,
            linewidth=2.2,
            zorder=3,
            ax=ax_pitch,
        )

        # Dorsal
        ax_pitch.annotate(
            str(numero)
            if numero is not None
            else "-",
            xy=(y, x),
            ha="center",
            va="center",
            fontsize=13,
            fontweight="bold",
            color=TEXT,
            zorder=4,
        )

        # Rating
        texto_rating = (
            f"{rating:.1f}"
            if rating is not None
            else "N/D"
        )

        ax_pitch.annotate(
            texto_rating,
            xy=(y, x),
            xytext=(0, -17),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=color_texto_rating,
            bbox={
                "boxstyle": "round,pad=0.22",
                "facecolor": color_rating,
                "edgecolor": PANEL,
                "linewidth": 1.4,
            },
            zorder=6,
        )

        # Nombre debajo del jugador
        ax_pitch.annotate(
            nombre,
            xy=(y, x),
            xytext=(0, -39),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=9,
            fontweight="bold",
            color=TEXT,
            zorder=5,
        )

    ruta = Path(
        ruta_salida
    )

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.savefig(
        ruta,
        dpi=100,
        facecolor=BACKGROUND,
    )

    plt.close(
        fig
    )

    return ruta