import matplotlib.pyplot as plt


import os
import urllib.request

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt


BACKGROUND = "#0B0F14"
PANEL = "#121820"

TEXT = "#F3F4F6"
MUTED_TEXT = "#8B95A5"

ACCENT = "#E63946"
ACCENT_DARK = "#B91C2B"

SECONDARY = "#C8CED6"

TRACK = "#1A2029"

DIVIDER = "#252B33"


RATING_BAD = "#D94A56"
RATING_AVERAGE = "#D6A83E"
RATING_GOOD = "#35A66F"
RATING_EXCELLENT = "#3182CE"
RATING_NA = "#5F6875"

RATING_TEXT_LIGHT = "#F3F4F6"
RATING_TEXT_DARK = "#0B0F14"


ACCOUNT_HANDLE = "@elrojoendatos"


# Tipografia editorial-deportiva. Se descarga una sola vez
# (queda cacheada en assets/fonts/) y se registra en
# matplotlib bajo su propio nombre de familia. Con eso alcanza:
# como todo el resto del codigo ya usa fontweight="bold" en
# los ax.text(), matplotlib elige sola el archivo Bold sin que
# tengamos que tocar ninguna de las 3 placas.
#
# Para cambiar de fuente en el futuro alcanza con reemplazar
# estas dos URLs por las de otra tipografia de Google Fonts
# (mismo mecanismo, ej. Oswald o Archivo Black).

FONT_FAMILY_FALLBACK = "DejaVu Sans"

FONT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "assets",
    "fonts",
)

FONT_SOURCES = {
    "BarlowCondensed-Regular.ttf": (
        "https://raw.githubusercontent.com/google/fonts/main/"
        "ofl/barlowcondensed/BarlowCondensed-Regular.ttf"
    ),
    "BarlowCondensed-Bold.ttf": (
        "https://raw.githubusercontent.com/google/fonts/main/"
        "ofl/barlowcondensed/BarlowCondensed-Bold.ttf"
    ),
}


def cargar_tipografia():
    """
    Descarga (con cache local) e instala Barlow Condensed.

    Si no hay conexion o algo falla, devuelve el fallback y
    el pipeline sigue funcionando igual - nunca se rompe un
    reporte por un problema de tipografia.
    """
    try:
        os.makedirs(
            FONT_DIR,
            exist_ok=True
        )

        for nombre_archivo, url in FONT_SOURCES.items():
            ruta = os.path.join(
                FONT_DIR,
                nombre_archivo
            )

            if not os.path.exists(ruta):
                urllib.request.urlretrieve(
                    url,
                    ruta
                )

            fm.fontManager.addfont(ruta)

        return "Barlow Condensed"

    except Exception as error:
        print(
            f"[theme] No se pudo cargar Barlow Condensed "
            f"({error}). Usando {FONT_FAMILY_FALLBACK}."
        )

        return FONT_FAMILY_FALLBACK


def aplicar_tema():
    familia = cargar_tipografia()

    plt.rcParams.update({
        "figure.facecolor": BACKGROUND,
        "axes.facecolor": BACKGROUND,
        "savefig.facecolor": BACKGROUND,

        "text.color": TEXT,
        "axes.labelcolor": TEXT,
        "xtick.color": MUTED_TEXT,
        "ytick.color": MUTED_TEXT,

        "font.family": familia,
        "font.size": 11,
    })