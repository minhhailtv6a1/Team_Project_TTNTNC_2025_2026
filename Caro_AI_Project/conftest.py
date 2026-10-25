import sys
from pathlib import Path

# Thêm thư mục gốc vào PYTHONPATH để pytest nhận diện được module core
sys.path.insert(0, str(Path(__file__).parent))