"""Collectibles recognition and attribute detection"""

from .recognizer import CollectibleRecognizer, identify_collectible
from .attribute_detector import AttributeDetector, detect_attributes

__all__ = [
    "CollectibleRecognizer",
    "identify_collectible",
    "AttributeDetector",
    "detect_attributes",
]
