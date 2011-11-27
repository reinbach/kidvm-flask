import sys
import os

prev_sys_path = list(sys.path)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

new_sys_path = [p for p in sys.path if p not in prev_sys_path]
for item in new_sys_path:
    sys.path.remove(item)
    sys.path[:0] = new_sys_path
    
from kidvm import app

if __name__ == '__main__':
    app.run(debug=True)