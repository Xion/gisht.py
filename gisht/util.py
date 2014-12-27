"""
Module with utility functions used throughout the code.
"""
from pathlib import Path


__all__ = ['ensure_path']


def ensure_path(path):
    """Ensures given path exists, creating all necessary directory levels.
    Does nothing otherwise.
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True)
