"""Casa Marina v6 = v5 overlays (logo/haze, sticker zoom, labels) on the wood-floor master.

The wood master (floor_composite.py output) is already in output order, so the EDL is the
identity; the sticker zoom stays correct because the first 113 output frames are the same
as the first 113 source frames.
Usage: python3 render_v6.py WOOD_MASTER.mp4 OUT.mp4
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
import render_v5  # noqa: F401  (installs the v5 labels/fonts into render_v4)
import render_v4 as V4

wood, out = sys.argv[1], sys.argv[2]
n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", wood], capture_output=True, text=True).stdout)
assert n == V4.N_OUT, (n, V4.N_OUT)
R.SRC = wood
V4.SEGS = [("all", 0, n, 0)]
V4.render(out)
