import os
from PyPDF2 import PdfMerger

pdf_files = [f for f in os.listdir('.') if f.startswith('Heatmap/Shear-Stress-') and f.endswith('-Heatmap-S12.pdf')]

def extract_position(filename):
    try:
        return int(filename.split('-')[2])
    except (IndexError, ValueError):
        return float('inf')

pdf_files_sorted = sorted(pdf_files, key=extract_position)

merger = PdfMerger()
for pdf in pdf_files_sorted:
    merger.append(pdf)

merger.write("./Shear-Stress-S12-All.pdf")
merger.close()
print(f"[INFO] Merge Finished {len(pdf_files_sorted)} -> Shear-Stress-S12-All.pdf")