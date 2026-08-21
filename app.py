import os
import json
import hashlib
from io import BytesIO
from datetime import datetime
import requests
from flask import Flask, request, render_template_string, send_file
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

app = Flask(__name__)

PDF_TEMPLATE = "certificate.pdf"

# =====================================================================
# 🌐 GOOGLE SHEETS LIVE CONFIG (DISABLED DURING LIVE RUSH TO PREVENT CRASH)
# =====================================================================
API_URL = "https://google.com"
USE_LIVE_API = False  # 🔴 SET TO TRUE ONLY AFTER THE WORKSHOP RUSH IS OVER
# =====================================================================

# PRE-LOAD TEMPLATE INTO RAM AT STARTUP (Saves massive disk CPU cycles)
if os.path.exists(PDF_TEMPLATE):
    with open(PDF_TEMPLATE, "rb") as f:
        TEMPLATE_BYTES = f.read()
else:
    TEMPLATE_BYTES = None

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Academic Certificate Registration</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; text-align: center; padding: 30px 15px; background: #0f111a; color: #ffffff; }
        .card { background: #1a1c26; padding: 25px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: inline-block; max-width: 450px; width: 100%; border: 1px solid #2d3142; box-sizing: border-box; }
        h2 { color: #ff4757; margin-top: 0; margin-bottom: 5px; font-size: 24px; }
        p { color: #a0a5c1; margin-bottom: 25px; font-size: 14px; }
        .form-group { text-align: left; margin-bottom: 15px; width: 100%; }
        label { display: block; font-size: 13px; color: #ff4757; margin-bottom: 5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        input { width: 100%; padding: 12px; border: 1px solid #3f445e; border-radius: 6px; font-size: 15px; background: #0f111a; color: #fff; box-sizing: border-box; }
        input:focus { border-color: #ff4757; outline: none; }
        button { background: #ff4757; color: white; border: none; padding: 14px; font-size: 16px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold; margin-top: 15px; transition: background 0.2s; }
        button:hover { background: #e84118; }
        .footer-note { font-size: 11px; color: #575f7d; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>CryptX Club</h2>
        <p>Cyber Security Workshop on Bug Bounty Hunting & Research Methodology</p>
        <form method="POST" action="/generate">
            <div class="form-group">
                <label>Full Name</label>
                <input type="text" name="username" placeholder="e.g. Rahul Sharma" required autocomplete="off">
            </div>
            <div class="form-group">
                <label>University Roll Number</label>
                <input type="text" name="uni_roll" placeholder="e.g. 2018642" required autocomplete="off">
            </div>
            <div class="form-group">
                <label>Section Roll Number</label>
                <input type="text" name="sec_roll" placeholder="e.g. 42" required autocomplete="off">
            </div>
            <div class="form-group">
                <label>Section</label>
                <input type="text" name="section" placeholder="e.g. CS-A" required autocomplete="off">
            </div>
            <div class="form-group">
                <label>Semester</label>
                <input type="text" name="semester" placeholder="e.g. 5th" required autocomplete="off">
            </div>
            <button type="submit">Verify & Generate Certificate</button>
        </form>
        <div class="footer-note">Secured by ANCPC</div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_FORM)

@app.route('/generate', methods=['POST'])
def generate():
    user_name = request.form.get('username', '').strip()
    uni_roll = request.form.get('uni_roll', '').strip()
    sec_roll = request.form.get('sec_roll', '').strip()
    section = request.form.get('section', '').strip()
    semester = request.form.get('semester', '').strip()

    if not all([user_name, uni_roll, sec_roll, section, semester]):
        return "All field variables are strictly mandatory.", 400

    user_payload = {
        "name": user_name,
        "uni_roll": str(uni_roll),
        "sec_roll": str(sec_roll),
        "section": section,
        "semester": semester
    }

    assigned_hash = "GEU-ERROR"
    
    # Fast bypass processing engine selection
    if USE_LIVE_API:
        try:
            response = requests.post(API_URL, data=json.dumps(user_payload), headers={"Content-Type": "application/json"}, timeout=4)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    assigned_hash = result.get("generated_hash", "GEU-UNKNOWN")
        except Exception:
            pass

    # Instant Local Fallback (Used during the rush to handle traffic seamlessly)
    if assigned_hash in ["GEU-ERROR", "GEU-UNKNOWN"]:
        emergency_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        emergency_payload = f"{user_name}|{uni_roll}|{emergency_time}"
        assigned_hash = f"GEU-LIVE-{hashlib.sha256(emergency_payload.encode('utf-8')).hexdigest()[:6].upper()}"

    # Use pre-loaded RAM cache instead of opening disk file over and over
    if TEMPLATE_BYTES:
        reader = PdfReader(BytesIO(TEMPLATE_BYTES))
    elif os.path.exists(PDF_TEMPLATE):
        reader = PdfReader(PDF_TEMPLATE)
    else:
        return f"Error: Template master binary file '{PDF_TEMPLATE}' is missing from the server root.", 500
        
    writer = PdfWriter()
    first_page = reader.pages[0]
    
    a4_width, a4_height = landscape(A4)
    center_x = a4_width / 2

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(first_page.mediabox.width, first_page.mediabox.height))
    
    can.setFont("Helvetica", 24)
    can.drawCentredString(center_x, 280, user_name)
    
    can.setFont("Helvetica", 10)
    can.setFillColorRGB(0.4, 0.4, 0.4)
    can.drawCentredString(center_x, 40, f"VERIFICATION ID: {assigned_hash}")
    
    can.save()
    packet.seek(0)
    
    text_layer_pdf = PdfReader(packet)
    first_page.merge_page(text_layer_pdf.pages[0])
    writer.add_page(first_page)
    
    for page_num in range(1, len(reader.pages)):
        writer.add_page(reader.pages[page_num])
        
    output_pdf = BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    
    clean_name = "".join(c for c in user_name if c.isalnum() or c in (' ', '_', '-')).strip()
    return send_file(
        output_pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Certificate_{clean_name}.pdf"
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
