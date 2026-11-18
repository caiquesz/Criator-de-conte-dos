"""Clean version of the v5 cut (no zoom, logo, haze or labels) + per-shot export, as AI input."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_v5  # noqa: F401  (sets fonts/labels; we bypass them)
import render_v4 as V4
V4.needs_processing = lambda k, s: False
out = sys.argv[1]
V4.render(out)
