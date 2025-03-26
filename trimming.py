import os
import pikepdf

directory = "/home/vansh/work/sarvam/rd-tablebench-sp/data/pdfs_sp"

for filename in os.listdir(directory):
    # print("reached here")
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(directory, filename)
        with pikepdf.open(pdf_path) as pdf:
            if len(pdf.pages) > 1:
                new_pdf = pikepdf.Pdf.new()
                new_pdf.pages.append(pdf.pages[0])
                new_pdf.save(pdf_path)  # Overwrites the original file
                print(f"Trimmed {filename} to 1 page.")
