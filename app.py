import os
import uuid
import csv
from io import BytesIO
from datetime import datetime
from flask import Flask, request, render_template_string, send_file
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape

app = Flask(__name__)

# System File/Folder Configurations
PDF_TEMPLATE = "certificate.pdf"
OUTPUT_FOLDER = "issued_certificates"
LOG_FILE = "issued_certificates.csv"

# Create required directory and database tracking file structural fallbacks
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Unique_ID", "Name", "Saved_Filename"])

# UI Presentation Layout Asset
HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claim Your Certificate</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; text-align: center; padding: 40px 20px; background: #0f111a; color: #ffffff; }
        .card { background: #1a1c26; padding: 30px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: inline-block; max-width: 400px; width: 100%; border: 1px solid #2d3142; }
        h2 { color: #ff4757; margin-bottom: 5px; }
        input[type="text"] { width: 90%; padding: 12px; margin: 20px 0; border: 1px solid #3f445e; border-radius: 6px; font-size: 16px; background: #0f111a; color: #fff; text-align: center; }
        input[type="text"]:focus { border-color: #ff4757; outline: none; }
        button { background: #ff4757; color: white; border: none; padding: 14px; font-size: 16px; border-radius: 6px; cursor: pointer; width: 96%; font-weight: bold; transition: 0.2s; }
        button:hover { background: #e84118; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Graphic Era University</h2>
        <p style="color: #a0a5c1;">Cyber Security Workshop</p>
        <form method="POST" action="/generate">
            <input type="text" name="username" placeholder="Enter Your Full Name" required autocomplete="off">
            <button type="submit">Claim Dynamic PDF</button>
        </form>
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
    if not user_name or len(user_name) > 50:
        return "Invalid Name Input", 400

    # 1. Generate Unique Verification Engine Details
    unique_id = f"GEU-{uuid.uuid4().hex[:6].upper()}"
    clean_name = "".join(c for c in user_name if c.isalnum() or c in (' ', '_', '-')).strip()
    output_filename = f"Certificate_{clean_name}_{unique_id}.pdf"
    disk_save_path = os.path.join(OUTPUT_FOLDER, output_filename)

    # Log parameters to base registry sheet immediately
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), unique_id, user_name, output_filename])

    # 2. Extract Template dimensions
    reader = PdfReader(PDF_TEMPLATE)
    writer = PdfWriter()
    first_page = reader.pages[0]
    
    a4_width, a4_height = landscape(A4)
    center_x = a4_width / 2

    # 3. Create the text overlay vector layer inside a memory stream
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(first_page.mediabox.width, first_page.mediabox.height))
    
    # Stamp Name (Configured to use Default Helvetica font, text size 24, Height 280)
    can.setFont("Helvetica", 24)
    can.drawCentredString(center_x, 280, user_name)
    
    # Stamp Verification Security Identification near the bottom edge context
    can.setFont("Helvetica", 10)
    can.setFillColorRGB(0.4, 0.4, 0.4)
    can.drawCentredString(center_x, 40, f"Verification Security ID: {unique_id}")
    
    can.save()
    packet.seek(0)
    
    # 4. Merge overlay context with original graphic background template
    text_layer_pdf = PdfReader(packet)
    first_page.merge_page(text_layer_pdf.pages[0])
    writer.add_page(first_page)
    
    # Process remaining background page structures if they exist
    for page_num in range(1, len(reader.pages)):
        writer.add_page(reader.pages[page_num])
        
    # 5. Dual Output Engine: Save to server disk inside separate folder 
    with open(disk_save_path, "wb") as disk_file:
        writer.write(disk_file)
        
    # 6. Stream file memory payload straight to user download pipeline
    output_pdf = BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    
    return send_file(
        output_pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Certificate_{clean_name}.pdf"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
