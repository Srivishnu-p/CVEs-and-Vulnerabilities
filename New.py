from flask import Flask, render_template, request, redirect, url_for, send_file
import requests
import xml.etree.ElementTree as ET
import time

app = Flask(__name__)

# Login to Qualys and return session
def login():
    session = requests.Session()
    payload = {
        'action': 'login',
        'username': 'ajsksks',
        'password': 'djwkekehdkd'
    }
    response = session.post('https://qualysapi.qualys.com/api/2.0/fo/session/', data=payload)
    if "Logged in" in response.text:
        return session
    else:
        raise Exception("Login failed!")

# Logout from Qualys
def logout(session):
    payload = {'action': 'logout'}
    session.post('https://qualysapi.qualys.com/api/2.0/fo/session/', data=payload)
    session.close()

# Launch scan
def launch_scan(session, target_ip):
    payload = {
        'action': 'launch',
        'ip': target_ip,
        'iscanner_name': 'denga',
        'priority': '12'
    }
    response = session.post('https://qualysapi.qualys.com/api/2.0/fo/scan/', data=payload)
    xml_response = ET.fromstring(response.text)
    scan_ref = None
    for elem in xml_response.findall('.//ITEM'):
        if elem[0].text == 'REFERENCE':
            scan_ref = elem[1].text
    return scan_ref

# Launch report
def launch_report(session, scan_ref, report_type, report_title):
    payload = {
        'action': 'launch',
        'report_type': 'Scan',
        'template_id': '4259874',
        'output_format': report_type,
        'report_refs': scan_ref,
        'report_title': report_title
    }
    response = session.post('https://qualysapi.qualys.com/api/2.0/fo/report/', data=payload)
    xml_response = ET.fromstring(response.text)
    report_id = None
    for elem in xml_response.findall('.//ITEM'):
        if elem[0].text == 'ID':
            report_id = elem[1].text
    return report_id

# Download report
def download_report(session, report_id):
    payload = {'action': 'fetch', 'id': report_id}
    response = session.post('https://qualysapi.qualys.com/api/2.0/fo/report/', data=payload)
    file_path = f"Scan_Report_{report_id}.pdf"
    with open(file_path, "wb") as file:
        file.write(response.content)
    return file_path

# Flask Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/launch_scan', methods=['POST'])
def launch_scan_ui():
    session = login()
    target_ip = request.form['target_ip']
    scan_ref = launch_scan(session, target_ip)
    logout(session)
    return f"Scan launched successfully! Scan Reference: {scan_ref}"

@app.route('/generate_report', methods=['POST'])
def generate_report_ui():
    session = login()
    scan_ref = request.form['scan_ref']
    report_type = request.form['report_type']
    report_title = request.form['report_title']
    report_id = launch_report(session, scan_ref, report_type, report_title)
    logout(session)
    return f"Report generated successfully! Report ID: {report_id}"

@app.route('/download_report/<report_id>')
def download_report_ui(report_id):
    session = login()
    file_path = download_report(session, report_id)
    logout(session)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
