from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import os

input_path = r"d:\work\civil_exam_aid\icon_designs\option_lighthouse_job_hunt.svg"
output_path = r"d:\work\civil_exam_aid\icon_designs\option_lighthouse_job_hunt.png"

try:
    print(f"Converting {input_path}...")
    drawing = svg2rlg(input_path)
    renderPM.drawToFile(drawing, output_path, fmt="PNG")
    print(f"Successfully converted to {output_path}")
except Exception as e:
    print(f"Error converting: {e}")
