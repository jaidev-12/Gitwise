"""Terminal branding: a small staged intro + colored chat roles.

The beat this is going for: a little desk lamp hops in, lands right where
the first "I" in GITWISE would be (standing in for the letter, the way a
mascot lands "in" a wordmark), switches on, and its light reveals the rest
of the logo around it. Ends on a settled title card with a permanent
git-commit-graph mark (the actual nod to git/GitHub) + credit.

The lamp is an original, generic silhouette (bulb / neck / base) - not a
reproduction of any specific studio's character design - just borrowing the
general "mascot hops in and lights up the sign" beat.
"""
import shutil
import time

import pyfiglet
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

_WORD = "GITWISE"
_FONT = "big"
_LOGO = pyfiglet.figlet_format(_WORD, font=_FONT)
_LOGO_LINES = _LOGO.rstrip("\n").split("\n")
_LOGO_HEIGHT = len(_LOGO_LINES)
_LOGO_WIDTH = max(len(line) for line in _LOGO_LINES)

_GRAPH_MARK = "o───o───o"


def _letter_span(letter_index: int) -> tuple[int, int]:
    """Column range (start, end) of the letter at `letter_index` in the
    rendered word, found by diffing successive prefix renders."""
    before = pyfiglet.figlet_format(_WORD[:letter_index], font=_FONT).rstrip("\n").split("\n")
    upto = pyfiglet.figlet_format(_WORD[: letter_index + 1], font=_FONT).rstrip("\n").split("\n")
    start = max((len(l) for l in before), default=0) if _WORD[:letter_index] else 0
    end = max(len(l) for l in upto)
    return start, end


# Land on the second "I" in GITWISE.
_SECOND_I_INDEX = _WORD.index("I", _WORD.index("I") + 1)
_GAP_START, _GAP_END = _letter_span(_SECOND_I_INDEX)

# Blank out that letter's columns in every row, leaving a socket for the lamp.
_LOGO_LINES_GAPPED = [
    line.ljust(_LOGO_WIDTH)[: _GAP_START] + " " * (_GAP_END - _GAP_START) + line.ljust(_LOGO_WIDTH)[_GAP_END:]
    for line in _LOGO_LINES
]

# --- The lamp itself: bulb, neck, base. Sized to match the logo's height so
# it can drop straight into the letter socket. ---
_LAMP_OFF = [
    "  _  ",
    " (o) ",
    "  |  ",
    "  |  ",
    "  |  ",
    "  |  ",
    " /_\\ ",
    "     ",
][: _LOGO_HEIGHT]
_LAMP_ON = [
    "  _  ",
    " (\u2609) ",
    "  |  ",
    "  |  ",
    "  |  ",
    "  |  ",
    " /_\\ ",
    "     ",
][: _LOGO_HEIGHT]
while len(_LAMP_OFF) < _LOGO_HEIGHT:
    _LAMP_OFF.append(" " * 5)
    _LAMP_ON.append(" " * 5)
_LAMP_WIDTH = max(len(l) for l in _LAMP_OFF)

# In-air poses used while hopping (shorter/squashed, don't need to match the
# logo height - only the final docked pose does).
_HOP_POSES = {
    "crouch": ["      ", " (_o_)", " /___\\"],
    "normal": ["  _  ", " (o) ", "  |  ", " /_\\ "],
    "squash": ["  ___  ", " (_o_) ", " /___\\ "],
    "stretch": ["  _  ", " ( ) ", " (o) ", "  |  ", "  |  ", " /_\\ "],
    "stretch_tall": ["  _  ", " ( ) ", " ( ) ", " (o) ", "  |  ", "  |  ", "  |  ", " /_\\ "],
}


def _ease_in_out(t: float) -> float:
    """Smoothstep - slow to start, fast in the middle, slow to finish."""
    return t * t * (3 - 2 * t)


def _hpad(lines: list[str], width: int) -> list[str]:
    return [l.ljust(width) for l in lines]


def _canvas_line(text_row: str, width: int) -> str:
    return text_row[:width].ljust(width)


def _hop_frame(x: int, canvas_width: int, pose: str, y_offset: int, air_rows: int) -> Text:
    frame = _hpad(_HOP_POSES[pose], max(len(l) for l in _HOP_POSES[pose]))
    rows = [""] * y_offset + frame + [""] * max(0, air_rows - y_offset)
    lines = []
    for row in rows:
        lines.append(_canvas_line(" " * max(0, x) + row, canvas_width) if row else "")
    return Text("\n".join(lines), style="bold yellow")


def _stage_lamp_hop(live: Live, term_width: int, target_x: int) -> None:
    """Hop the lamp in from off-screen left with real weight to it:
    a crouch (anticipation) before each leap, a smooth eased arc instead of
    a straight triangle, a big dramatic stomp for the final landing, and a
    springy settle-wobble once it's down - the classic squash/stretch,
    anticipation, and ease-in-ease-out beats."""
    air_rows = 5
    half = max((target_x - 2) // 2, 1)
    # (start_x, end_x, peak_height 0..1, frames, stretch_pose)
    hops = [
        (2, 2 + half, 0.55, 14, "stretch"),
        (2 + half, target_x, 1.0, 20, "stretch_tall"),
    ]
    for start_x, end_x, peak, frames, stretch_pose in hops:
        # anticipation: crouch in place before launching
        live.update(Align.left(_hop_frame(start_x, term_width, "crouch", air_rows, air_rows)))
        time.sleep(0.14)

        for step in range(frames + 1):
            t = step / frames
            eased_x = _ease_in_out(t)
            x = int(start_x + (end_x - start_x) * eased_x)
            # smooth parabola for height, peaking at the midpoint
            arc = 4 * peak * t * (1 - t)
            y_offset = round(air_rows * (1 - min(arc, 1.0)))
            if t < 0.12:
                pose = "crouch"
            elif arc > 0.75:
                pose = stretch_pose
            elif t > 0.88:
                pose = "squash"
            else:
                pose = "normal"
            live.update(Align.left(_hop_frame(x, term_width, pose, y_offset, air_rows)))
            time.sleep(1 / 26)

    # the stomp: hold the squash a beat so the landing actually registers
    live.update(Align.left(_hop_frame(target_x, term_width, "squash", air_rows, air_rows)))
    time.sleep(0.18)

    # settle wobble - a couple of decreasing rebounds, like a spring settling
    for rebound_height, dur in ((2, 0.09), (1, 0.08)):
        live.update(Align.left(_hop_frame(target_x, term_width, "normal", air_rows - rebound_height, air_rows)))
        time.sleep(dur)
        live.update(Align.left(_hop_frame(target_x, term_width, "normal", air_rows, air_rows)))
        time.sleep(dur)


def _compose(logo_lines: list[str], lamp_lines: list[str], logo_margin: int, lamp_on: bool) -> Text:
    """Overlay the lamp into the logo's letter-socket and return one colored
    frame, both left-padded to sit at the same spot they occupied while
    hopping/reveal happen in absolute console coordinates."""
    text = Text()
    lamp_x = logo_margin + _GAP_START + ((_GAP_END - _GAP_START) - _LAMP_WIDTH) // 2
    lamp_style = "bold yellow" if lamp_on else "grey50"
    for i, row in enumerate(logo_lines):
        padded = " " * logo_margin + row
        lamp_row = lamp_lines[i] if i < len(lamp_lines) else ""
        before = padded[:lamp_x]
        after = padded[lamp_x + _LAMP_WIDTH :]
        text.append(before, style="bold cyan")
        text.append(lamp_row.ljust(_LAMP_WIDTH), style=lamp_style)
        text.append(after, style="bold cyan")
        text.append("\n")
    return text


def _stage_dock_and_light(live: Live, logo_margin: int) -> None:
    """Lamp is in place: flicker on, then the rest of the logo fades in
    around it."""
    # flicker
    for on in (False, True, False, True, True):
        frame = _compose(_LOGO_LINES_GAPPED, _LAMP_ON if on else _LAMP_OFF, logo_margin, on)
        live.update(Align.left(frame))
        time.sleep(0.12 if on else 0.08)

    # rest of the wordmark fades in, dim -> bright
    dim_lines = [
        "".join(ch if ch == " " else "\u00b7" for ch in row) for row in _LOGO_LINES_GAPPED
    ]
    for lines, pause in ((dim_lines, 0.12), (_LOGO_LINES_GAPPED, 0.0)):
        frame = _compose(lines, _LAMP_ON, logo_margin, True)
        live.update(Align.left(frame))
        time.sleep(pause)
    time.sleep(0.25)


def show_intro_animation(console: Console, credit: str = "jaidev-12 & 4ravind-b") -> None:
    """Play the staged intro: a lamp hops in, lands where the first "I" in
    GITWISE would be, switches on, and lights up the rest of the wordmark.

    Purely cosmetic branding - safe to skip/fail silently on any terminal quirks.
    """
    try:
        term_width = shutil.get_terminal_size().columns
        term_height = shutil.get_terminal_size().lines
        if term_width < _LOGO_WIDTH + 4 or term_height < _LOGO_HEIGHT + 8:
            return  # terminal too small for the effect, skip straight to the panel

        logo_margin = max((term_width - _LOGO_WIDTH) // 2, 0)
        lamp_x = logo_margin + _GAP_START + ((_GAP_END - _GAP_START) - _LAMP_WIDTH) // 2

        with Live(console=console, refresh_per_second=24, transient=True) as live:
            _stage_lamp_hop(live, term_width, lamp_x)
            _stage_dock_and_light(live, logo_margin)
    except Exception:
        pass  # never let a cosmetic animation crash the CLI

    console.print(Align.center(_compose(_LOGO_LINES_GAPPED, _LAMP_ON, 0, True)))
    console.print(
        Align.center(
            Panel(
                f"[bold cyan]GitWise[/bold cyan]   [green]{_GRAPH_MARK}[/green]\n"
                f"[dim]Understand any repo in plain English[/dim]\n"
                f"[dim]by {credit}[/dim]",
                border_style="magenta",
                width=48,
            )
        )
    )


def print_assistant_label(console: Console) -> None:
    """Print a label before the model's answer, visually distinct from the user."""
    console.print("[bold magenta]GitWise:[/bold magenta]")
