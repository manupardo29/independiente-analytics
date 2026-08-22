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



def aplicar_tema():
    plt.rcParams.update({
        "figure.facecolor": BACKGROUND,
        "axes.facecolor": BACKGROUND,
        "savefig.facecolor": BACKGROUND,

        "text.color": TEXT,
        "axes.labelcolor": TEXT,
        "xtick.color": MUTED_TEXT,
        "ytick.color": MUTED_TEXT,

        "font.family": "DejaVu Sans",
        "font.size": 11,
    })