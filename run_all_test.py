import os

os.system("")
statusColor = '\033[92m'
warningColor = '\033[93m'
endColor = '\033[0m'

print(f"{warningColor}========== run all tests =========={endColor}")
cmd_run_tests = "cd dist3 && ctest -C Release"
print(f"{statusColor}[command] {cmd_run_tests}{endColor}")
os.system(cmd_run_tests)
