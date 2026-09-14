"""Five photos are available: north, south, east, west, and top.

A simple gable does not need four corners on every photo. The top photo holds
the run (and the ridge in plan). One profile photo that looks along the ridge
holds the rise. Pitch is rise over that run. The facing photo shows which
way the plane drains. More corners and more views help on a complex roof;
they are not a gate for a simple one.
"""

from __future__ import annotations

# heading: direction the camera looks. drain_deg: compass bearing water runs
# on the planes that face this camera. 0 is north, 90 is east. Top has no
# facing drain; it holds the run.
VIEWS = {
    "top": {"heading": 0, "tilt": 0, "drain_deg": None, "label": "Top", "holds": "run"},
    "north": {"heading": 180, "tilt": 45, "drain_deg": 0, "label": "North", "holds": "face"},
    "east": {"heading": 270, "tilt": 45, "drain_deg": 90, "label": "East", "holds": "face"},
    "south": {"heading": 0, "tilt": 45, "drain_deg": 180, "label": "South", "holds": "face"},
    "west": {"heading": 90, "tilt": 45, "drain_deg": 270, "label": "West", "holds": "face"},
}


def pitch_from_profile(rise_ft: float, run_ft: float) -> str | None:
    """n/12 from the rise in a side photo and the run in the top photo."""
    if run_ft is None or rise_ft is None or run_ft <= 0 or rise_ft < 0:
        return None
    n = int(round(12.0 * float(rise_ft) / float(run_ft)))
    n = max(0, min(24, n))
    return f"{n}/12"


def profile_views(drain_deg: float) -> tuple[str, str]:
    """Side photos that show the rise. The run for the same triangle is always top.

    A north-draining plane has an east-west ridge. The rise is in the east
    and west photos. The north photo shows the face. The top photo is the run.
    """
    d = float(drain_deg) % 360.0
    along = min(d % 180.0, 180.0 - (d % 180.0))
    if along <= 45.0:
        return ("east", "west")
    return ("north", "south")


def facing_view(drain_deg: float) -> str:
    d = float(drain_deg) % 360.0
    if d < 45 or d >= 315:
        return "north"
    if d < 135:
        return "east"
    if d < 225:
        return "south"
    return "west"
