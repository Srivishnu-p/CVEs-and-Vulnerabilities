from flask import Flask, request, render_template, jsonify, make_response
import pandas as pd
import socket
import os
import re
import requests
from datetime import datetime
import json

app = Flask(_name_)

# Path to the Excel file in the same directory
EXCEL_FILE_PATH = os.path.join(os.path.dirname(_file_), "data.xlsx")
SESSION_FILE = os.path.join(os.path.dirname(_file_), "qualys_session.json")

# Qualys API credentials
QUALYS_BASE_URL = "https://qualysapi.qualys.com/api/2.0/fo/"
QUALYS_USERNAME = "your_qualys_username"
QUALYS_PASSWORD = "your_qualys_password"

def split_input(input_data):
    return [item.strip() for item in re.split(r'[,\s\n]+', input_data) if item.strip()]

def save_session(cookie):
    with open(SESSION_FILE, 'w') as f:
        json.dump({'cookie': cookie, 'timestamp': datetime.now().isoformat()}, f)

def load_session():
    try:
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
            return data['cookie']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None

def delete_session():
    try:
        os.remove(SESSION_FILE)
    except FileNotFoundError:
        pass

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    names = []
    session_active = False if load_session() is None else True

    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        if "Name" in df.columns:
            names = df["Name"].drop_duplicates().tolist()
    except Exception as e:
        error = f"Error reading the file: {e}"

    if request.method == 'POST':
        if 'qualys_login' in request.form:
            # Login to Qualys
            try:
                response = requests.post(
                    f"{QUALYS_BASE_URL}session/",
                    data={"action": "login", "username": QUALYS_USERNAME, "password": QUALYS_PASSWORD},
                    verify=False
                )
                if response.status_code == 200:
                    cookie = response.headers.get('Set-Cookie')
                    if cookie:
                        save_session(cookie)
                        session_active = True
                        result = "Qualys login successful!"
                    else:
                        error = "No session cookie received"
                else:
                    error = f"Login failed: {response.status_code} - {response.text}"
            except Exception as e:
                error = f"Login error: {str(e)}"

        elif 'qualys_logout' in request.form:
            # Logout from Qualys
            cookie = load_session()
            if cookie:
                try:
                    response = requests.post(
                        f"{QUALYS_BASE_URL}session/",
                        headers={"Cookie": cookie},
                        data={"action": "logout"},
                        verify=False
                    )
                    if response.status_code == 200:
                        result = "Qualys logout successful!"
                    else:
                        error = f"Logout failed: {response.status_code} - {response.text}"
                except Exception as e:
                    error = f"Logout error: {str(e)}"
                finally:
                    delete_session()
                    session_active = False

        elif 'launch_scan' in request.form:
            # Launch scan using existing session
            cookie = load_session()
            if not cookie:
                error = "No active Qualys session. Please login first."
            else:
                scan_title = request.form['scan_title']
                target_ip = request.form['target_ip']
                current_date = datetime.now().strftime("%d-%b")
                scan_title = f"{scan_title}rescan{current_date}"

                try:
                    response = requests.post(
                        f"{QUALYS_BASE_URL}scan/",
                        headers={
                            "Cookie": cookie,
                            "X-Requested-With": "agent_sp3"
                        },
                        data={
                            "action": "launch",
                            "scan_title": scan_title,
                            "ip": target_ip,
                            "option_id": "1189927",
                            "iscanner_name": "denisal",
                            "priority": "0"
                        },
                        verify=False
                    )
                    if response.status_code == 200:
                        result = f"Scan launched successfully! Scan Title: {scan_title}"
                    else:
                        error = f"Scan failed: {response.status_code} - {response.text}"
                except Exception as e:
                    error = f"Scan error: {str(e)}"

        # [Previous DNS/IP resolution functions remain unchanged...]

    return render_template(
        'index.html',
        result=result,
        error=error,
        names=names,
        session_active=session_active
    )

# [Previous /get_ips route remains unchanged...]

if _name_ == '_main_':
    app.run(debug=True)
