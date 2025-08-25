import os

os.system("")
statusColor = '\033[92m'
warningColor = '\033[93m'
endColor = '\033[0m'

print(f"{warningColor}========== config cmake =========={endColor}")
cmd_config_cmake = "cmake -S src -B dist3 -G \"Visual Studio 17 2022\" -A x64"
print(f"{statusColor}[command] {cmd_config_cmake}{endColor}")
os.system(cmd_config_cmake)

print(f"{warningColor}========== build project =========={endColor}")
cmd_build_project = "cmake --build dist3 --config Release -j"
print(f"{statusColor}[command] {cmd_build_project}{endColor}")
os.system(cmd_build_project)

