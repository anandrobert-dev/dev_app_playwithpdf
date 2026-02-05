from pypdf import PdfReader, PdfWriter
import os

def split_pdf_by_ranges(input_pdf, ranges, output_dir):
    try:
        reader = PdfReader(input_pdf)

        for start, end, name in ranges:
            writer = PdfWriter()
            for i in range(start - 1, end):  # 0-indexed
                if i < len(reader.pages):
                    writer.add_page(reader.pages[i])
            with open(os.path.join(output_dir, name), "wb") as f:
                writer.write(f)
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

