import os
import sys
from ui import main

path = os.path.dirname(os.path.abspath(sys.executable))

if __name__ == "__main__":
    main(path)
