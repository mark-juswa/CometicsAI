"""Reuse the existing pinned private Makeup GPU preparation, with no service."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.makeup_quality_bootstrap import bootstrap

if __name__ == "__main__":
    bootstrap(runner="scripts/makeup_reference_diagnostic.py")
