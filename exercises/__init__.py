# fitness_tracker/exercises/__init__.py
from .pushup import PushupTracker
from .squat import SquatTracker
from .bicep_curl import BicepCurlTracker

EXERCISE_TRACKERS = {
    "Push-up": PushupTracker,
    "Squat": SquatTracker,
    "Bicep Curl": BicepCurlTracker
}