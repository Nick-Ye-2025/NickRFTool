import sys
import tkinterdnd2
from pathlib import Path

dnd_path = Path(tkinterdnd2.__file__).parent
print(f"tkinterdnd2路径: {dnd_path}")
print(f"tkdnd库路径: {dnd_path / 'tkdnd'}")