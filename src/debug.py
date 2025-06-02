import sys

print(f"--- DEBUG INFO ---")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"sys.path:")
for p in sys.path:
    print(p)
print(f"--- END DEBUG INFO ---")

import pandas as pd  # Esta línea seguirá causando el error si el problema persiste
# ... el resto de tu código
