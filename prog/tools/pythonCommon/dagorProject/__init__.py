"""Game projects built with this engine, wherever they are: engine.blk, the generated engine glue (setup) and the
project.py commands (cli). New projects are created from templates/ by dng.py new in the engine root (create)."""
from .engine import ENGINE_BLK, ProjectError, read_engine_root, write_engine_blk
from .glue import Project, setup
