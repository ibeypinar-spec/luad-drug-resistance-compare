import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd

WORK_DIR = "G:\\Drive'\u0131m\\\u00c7al\u0131\u015fma\\Aktif \u00c7al\u0131\u015fmalar\\9. A\u00e7\u0131k eri\u015fim veri \u00e7al\u0131\u015fmalar\u0131\\LUAD Drug Resistance Study"
RESULTS_DIR = os.path.join(WORK_DIR, "results")

print("WORK_DIR exists:", os.path.isdir(WORK_DIR))
print("RESULTS_DIR exists:", os.path.isdir(RESULTS_DIR))
print()

# Check Excel files
for fname in ["LUAD_Faz2_Results.xlsx", "LUAD_Faz2b_Results.xlsx"]:
    fpath = os.path.join(RESULTS_DIR, fname)
    if os.path.exists(fpath):
        xl = pd.ExcelFile(fpath)
        print(f"{fname}: {xl.sheet_names}")
    else:
        print(f"{fname}: NOT FOUND")

print()
# Check PNG files
pngs = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.png')]
print("PNG files:", sorted(pngs))
