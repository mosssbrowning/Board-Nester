
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO

st.set_page_config(page_title="Moss Board Material Calculator and Optimizer", layout="wide")

sheet_width, sheet_height = 48, 96
sheet_area = sheet_width * sheet_height

st.title("📏 Moss Board Material Calculator and Optimizer")

uploaded_file = st.file_uploader("Upload Excel file with columns: Length (in), Height (in), Quantity", type=["xlsx"])

def best_fit_per_sheet(length, height):
    fit_original = (sheet_width // length) * (sheet_height // height)
    fit_rotated = (sheet_width // height) * (sheet_height // length)
    return max(fit_original, fit_rotated)

def nest_parts(parts, sheet_width, sheet_height):
    sheets = []
    current_sheet = []
    space_map = [(0, 0, sheet_width, sheet_height)]

    for length, height in parts:
        placed = False
        for idx, (x, y, w, h) in enumerate(space_map):
            fits_normally = length <= w and height <= h
            fits_rotated = height <= w and length <= h

            if fits_normally or fits_rotated:
                if fits_rotated:
                    length, height = height, length

                current_sheet.append((x, y, length, height))
                del space_map[idx]
                space_map.append((x + length, y, w - length, height))
                space_map.append((x, y + height, w, h - height))
                placed = True
                break

        if not placed:
            sheets.append(current_sheet)
            current_sheet = [(0, 0, length, height)]
            space_map = [(length, 0, sheet_width - length, height), (0, height, sheet_width, sheet_height - height)]

    sheets.append(current_sheet)
    return sheets

def create_pdf_layout(sheets):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    for i, sheet in enumerate(sheets):
        c.drawString(30, 750, f"Sheet {i + 1}")
        for (x, y, w, h) in sheet:
            sx, sy, sw, sh = x * 5, y * 5, w * 5, h * 5
            c.rect(sx + 50, sy + 100, sw, sh)
            c.drawString(sx + 50 + sw / 2 - 10, sy + 100 + sh / 2, f"{int(w)}×{int(h)}")
        c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    parts_to_nest = []
    total_cut_inches = 0
    for _, row in df.iterrows():
        l, h, q = row["Length (in)"], row["Height (in)"], int(row["Quantity"])
        parts_to_nest.extend([(l, h)] * q)
        total_cut_inches += ((2 * l + 2 * h) * q)

    nested_sheets = nest_parts(parts_to_nest, sheet_width, sheet_height)
    total_part_area = sum(l * h for l, h in parts_to_nest)
    total_sheets_used = len(nested_sheets)
    total_sheet_area = total_sheets_used * sheet_area
    material_yield_percent = (total_part_area / total_sheet_area) * 100

    st.metric("Total 4×8 Sheets Required", total_sheets_used)
    st.metric("Material Yield (%)", f"{material_yield_percent:.2f}%")
    st.metric("Total Cut Inches", f"{int(total_cut_inches):,} in")

    if st.button("Download PDF Layout"):
        pdf_bytes = create_pdf_layout(nested_sheets)
        st.download_button(label="Download PDF", data=pdf_bytes, file_name="layout.pdf", mime="application/pdf")
