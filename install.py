import os
from pathlib import Path
import shutil

os.system("")
statusColor = '\033[92m'
warningColor = '\033[93m'
endColor = '\033[0m'

print(f"{warningColor}========== install =========={endColor}")
print(f"{statusColor}-- removing existing installation{endColor}")
install_folder = Path("install")
if install_folder.exists() and install_folder.is_dir():
    shutil.rmtree("install")
    print(f"{statusColor}-- removed install/{endColor}")

print(f"{statusColor}-- install to `install/`{endColor}")
cmd_install = "cmake --install dist3 --config Release --prefix install"
print(f"{statusColor}[command] {cmd_install}{endColor}")
os.system(cmd_install)