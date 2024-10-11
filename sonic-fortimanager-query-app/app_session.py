import os
from flask import Flask, jsonify, request, render_template_string, redirect, url_for
import requests
import sqlite3
import json
from config import FMGR_URL, DB_NAME, LOG_LEVEL, LOG_FILE, DEBUG, HOST, PORT, SSL_VERIFY, FMGR_USERNAME, FMGR_PASSWORD
import traceback
import logging
import sys
from io import StringIO
from dotenv import load_dotenv
from openpyxl import Workbook
from flask import send_file
# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL),
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(LOG_FILE),
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)

if not SSL_VERIFY:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logger.warning("SSL verification is disabled. This is not recommended for production use.")

app = Flask(__name__)
def export_to_excel():
    """Export VLAN 10 IPs to an Excel file."""
    logger.info("Exporting VLAN 10 IPs to Excel")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT device_name, ip_address FROM vlan10_ips")
        rows = c.fetchall()
        conn.close()

        if not rows:
            logger.warning("No VLAN 10 IPs found to export")
            return "No VLAN 10 IPs found to export", 404

        # Create an Excel workbook and sheet
        wb = Workbook()
        ws = wb.active
        ws.title = "VLAN 10 IPs"

        # Add headers
        ws.append(["Device Name", "IP Address"])

        # Add data rows
        for row in rows:
            ws.append([row["device_name"], row["ip_address"]])

        # Save the workbook to a file
        file_path = "vlan10_ips.xlsx"
        wb.save(file_path)
        logger.info(f"VLAN 10 IPs exported to {file_path}")

        return send_file(file_path, as_attachment=True)
    except sqlite3.Error as e:
        logger.error(f"Database error in export_to_excel: {str(e)}")
        return f"Database error: {str(e)}", 500
    except Exception as e:
        logger.error(f"Unexpected error in export_to_excel: {str(e)}")
        return f"Unexpected error: {str(e)}", 500
# Global variable to store the session token
session_token = None

def get_session_token():
    """Obtain a session token from FortiManager."""
    global session_token
    logger.info("Obtaining session token from FortiManager")
    login_payload = {
        "id": 1,
        "method": "exec",
        "params": [
            {
                "data": {
                    "user": FMGR_USERNAME,
                    "passwd": FMGR_PASSWORD
                },
                "url": "/sys/login/user"
            }
        ]
    }
    try:
        response = requests.post(FMGR_URL, json=login_payload, verify=SSL_VERIFY)
        response.raise_for_status()
        json_response = response.json()
        if 'session' in json_response:
            session_token = json_response['session']
            logger.info("Session token obtained successfully")
            return session_token
        else:
            logger.error("Failed to obtain session token")
            return None
    except Exception as e:
        logger.error(f"Error obtaining session token: {str(e)}")
        return None

def refresh_session_token():
    """Refresh the session token if it has expired."""
    global session_token
    session_token = get_session_token()
    if session_token is None:
        raise Exception("Failed to refresh session token")

# Database setup
def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database by creating the necessary table."""
    logger.info("Initializing database")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS vlan10_ips
              (id INTEGER PRIMARY KEY, device_name TEXT, ip_address TEXT)
              ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# Function to fetch VLAN 10 IPs from FortiManager
def fetch_vlan_10_ips():
    """Fetch VLAN 10 IPs from FortiManager and store them in the database."""
    logger.info("Fetching VLAN 10 IPs from FortiManager")
    try:
        session_token = get_session_token()
        if not session_token:
            return "Failed to obtain session token", 500

        # Query for FortiGate devices
        query_payload = {
            "method": "get",
            "params": [
                {
                    "url": "/dvmdb/device"
                }
            ],
            "session": session_token
        }

        response = requests.post(FMGR_URL, json=query_payload, verify=SSL_VERIFY)
        response_data = response.json()
        print(response_data)  # Temporary print statement to inspect the response structure

        if response.status_code != 200 or response_data.get("result")[0].get("status").get("code") != 0:
            if response_data.get("error", {}).get("message") == "Invalid session":
                logger.info("Session token expired, refreshing token")
                session_token = refresh_session_token()
                query_payload["session"] = session_token
                response = requests.post(FMGR_URL, json=query_payload, verify=SSL_VERIFY)
                response_data = response.json()

        devices = response_data.get("result")[0].get("data", [])
        vlan_10_ips = []

        for device in devices:
            device_name = device.get("name")
            logger.info(f"Querying interfaces for device: {device_name}")
            dev_query_payload = {
                "method": "get",
                "params": [
                    {
                        "url": f"/pm/config/device/{device_name}/global/system/interface"
                    }
                ],
                "session": session_token
            }
            response = requests.post(FMGR_URL, json=dev_query_payload, verify=SSL_VERIFY)
            interfaces = response.json().get("result")[0].get("data", [])
            for interface in interfaces:
                if interface.get("vlanid") == 10:
                    ip_address = interface.get("ip")
                    vlan_10_ips.append((device_name, ip_address))

        if not vlan_10_ips:
            logger.warning("No VLAN 10 IPs found for any device")
            return "No VLAN 10 IPs found", 404

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM vlan10_ips")
        c.executemany("INSERT INTO vlan10_ips (device_name, ip_address) VALUES (?, ?)", vlan_10_ips)
        conn.commit()
        conn.close()
        logger.info(f"VLAN 10 IPs stored in database: {vlan_10_ips}")

        return "VLAN 10 IPs fetched and stored successfully", 200
    except requests.RequestException as e:
        logger.error(f"Request error in fetch_vlan_10_ips: {str(e)}")
        return f"Request error: {str(e)}", 500
    except sqlite3.Error as e:
        logger.error(f"Database error in fetch_vlan_10_ips: {str(e)}")
        return f"Database error: {str(e)}", 500
    except Exception as e:
        logger.error(f"Unexpected error in fetch_vlan_10_ips: {str(e)}")
        return f"Unexpected error: {str(e)}", 500

@app.route('/')
def index():
    """Render the index page with buttons to fetch, retrieve, and export IPs."""
    logger.info("Received request to /")
    ssl_warning = "WARNING: SSL verification is disabled. This is not recommended for production use." if not SSL_VERIFY else ""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Arbys FortiManager Query App</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container mt-5">
        <h1 class="mb-4">Arbys FortiManager Query App</h1>
        <p class="text-danger font-weight-bold">{{ ssl_warning }}</p>
        <form action="{{ url_for('fetch_ips') }}" method="post" class="mb-3">
            <button type="submit" class="btn btn-primary">Fetch VLAN 10 IPs</button>
        </form>
        <form action="{{ url_for('get_ips') }}" method="get" class="mb-3">
            <button type="submit" class="btn btn-secondary">Retrieve VLAN 10 IPs</button>
        </form>
        <form action="{{ url_for('export_ips') }}" method="get" class="mb-3">
            <button type="submit" class="btn btn-success">Export VLAN 10 IPs to Excel</button>
        </form>
        <a href="{{ url_for('debug_api') }}" class="btn btn-link">Debug API Response</a>
        <a href="{{ url_for('debug_api_full') }}" class="btn btn-link">Debug API Response (Full)</a>
        <a href="{{ url_for('test_endpoints') }}" class="btn btn-link">Test API Endpoints</a>
        <a href="{{ url_for('check_token') }}" class="btn btn-link">Check Session Token</a>
        <a href="{{ url_for('user_info') }}" class="btn btn-link">Get User Info</a>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    """, ssl_warning=ssl_warning)
@app.route('/export_ips', methods=['GET'])
def export_ips():
    """Endpoint to export VLAN 10 IPs to an Excel file."""
    logger.info("Received request to /export_ips")
    message, status = export_to_excel()
    if status == 200:
        return message
    else:
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>Export VLAN 10 IPs Result</title>
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
        <div class="container mt-5">
            <h1 class="mb-4">Export VLAN 10 IPs Result</h1>
            <p>{{ message }}</p>
            <a href="{{ url_for('index') }}" class="btn btn-primary">Back to Home</a>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        </body>
        </html>
        """, message=message)
@app.route('/fetch_ips', methods=['POST'])
def fetch_ips():
    """Endpoint to fetch VLAN 10 IPs from FortiManager."""
    logger.info("Received request to /fetch_ips")
    message, status = fetch_vlan_10_ips()
    logger.info(f"Completed /fetch_ips request with status {status}")
    return render_template_string("""
    <h1>Fetch VLAN 10 IPs Result</h1>
    <p>{{ message }}</p>
    <a href="{{ url_for('index') }}">Back to Home</a>
    """, message=message)

@app.route('/get_ips', methods=['GET'])
def get_ips():
    """Endpoint to retrieve VLAN 10 IPs from the database."""
    logger.info("Received request to /get_ips")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM vlan10_ips")
        rows = c.fetchall()
        conn.close()
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>VLAN 10 IPs</title>
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
        <div class="container mt-5">
            <h1 class="mb-4">VLAN 10 IPs</h1>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Device Name</th>
                        <th>IP Address</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in rows %}
                    <tr>
                        <td>{{ row.id }}</td>
                        <td>{{ row.device_name }}</td>
                        <td>{{ row.ip_address }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <a href="{{ url_for('index') }}" class="btn btn-primary">Back to Home</a>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        </body>
        </html>
        """, rows=rows)
    except sqlite3.Error as e:
        logger.error(f"Database error in get_ips: {str(e)}")
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>Error</title>
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
        <div class="container mt-5">
            <h1 class="mb-4">Error</h1>
            <p class="text-danger">Database error: {{ error }}</p>
            <a href="{{ url_for('index') }}" class="btn btn-primary">Back to Home</a>
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        </body>
        </html>
        """, error=str(e))
@app.route('/debug_api', methods=['GET'])
def debug_api():
    """Endpoint to debug API response."""
    logger.info("Received request to /debug_api")
    query_payload = {
        "method": "get",
        "params": [
            {
                "url": "/dvmdb/device"
            }
        ],
        "session": session_token,
        "id": 1
    }
    try:
        response = requests.post(FMGR_URL, json=query_payload, verify=SSL_VERIFY)
        response.raise_for_status()
        json_response = response.json()
        logger.info(f"Debug API response: {json.dumps(json_response, indent=2)}")
        return render_template_string("""
        <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <title>Debug API Response</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="container mt-5">
        <h1 class="mb-4">Debug API Response</h1>
        <pre>{{ response }}</pre>
        <a href="{{ url_for('index') }}" class="btn btn-primary">Back to Home</a>
    </div>
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.4/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
    </body>
    </html>
    """, response=response)
    except Exception as e:
        logger.error(f"Error in debug_api: {str(e)}")
        return render_template_string("""
        <h1>Debug API Error</h1>
        <p>{{ error }}</p>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, error=str(e))

@app.route('/debug_api_full', methods=['GET'])
def debug_api_full():
    """Endpoint to debug API response with full logs."""
    logger.info("Received request to /debug_api_full")
    query_payload = {
        "method": "get",
        "params": [
            {
                "url": "/dvmdb/device"
            }
        ],
        "session": session_token,
        "id": 1
    }
    try:
        logger.info(f"Sending request to FortiManager: {FMGR_URL}")
        logger.info(f"Request payload: {json.dumps(query_payload, indent=2)}")
        response = requests.post(FMGR_URL, json=query_payload, verify=SSL_VERIFY)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        logger.info(f"Response content: {response.text}")

        response.raise_for_status()
        json_response = response.json()
        logger.info(f"Parsed JSON response: {json.dumps(json_response, indent=2)}")

        log_contents = StringIO()
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                log_contents = handler.stream.getvalue()
                break
        
        return render_template_string("""
        <h1>Debug API Response (Full)</h1>
        <h2>API Response:</h2>
        <pre>{{ response }}</pre>
        <h2>Full Logs:</h2>
        <pre>{{ logs }}</pre>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, response=json.dumps(json_response, indent=2), logs=log_contents)
    except Exception as e:
        logger.error(f"Error in debug_api_full: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        log_contents = StringIO()
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                log_contents = handler.stream.getvalue()
                break
        return render_template_string("""
        <h1>Debug API Error (Full)</h1>
        <p>{{ error }}</p>
        <h2>Full Logs:</h2>
        <pre>{{ logs }}</pre>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, error=str(e), logs=log_contents)

@app.route('/test_endpoints', methods=['GET'])
def test_endpoints():
    """Endpoint to test multiple FortiManager API endpoints."""
    logger.info("Received request to /test_endpoints")
    
    test_urls = [
        "/dvmdb/device",
        "/cli/global/system/admin/setting",
        "/dvmdb/adom",
        "/pm/config/adom/_adom_/obj/firewall/address",
        "/pm/config/global/obj/firewall/address",
        "/sys/status",
        "/sys/proxy/json",
        "/sys/global"
    ]
    
    results = []
    for url in test_urls:
        query_payload = {
            "method": "get",
            "params": [
                {
                    "url": url
                }
            ],
            "session": session_token,
            "id": 1
        }
        try:
            logger.info(f"Testing endpoint: {url}")
            response = requests.post(FMGR_URL, json=query_payload, verify=SSL_VERIFY)
            response.raise_for_status()
            json_response = response.json()
            status = json_response.get('result', [{}])[0].get('status', {})
            results.append({
                "url": url,
                "status_code": status.get('code'),
                "message": status.get('message'),
                "response": json_response
            })
        except Exception as e:
            logger.error(f"Error testing endpoint {url}: {str(e)}")
            results.append({
                "url": url,
                "error": str(e)
            })
    
    return render_template_string("""
    <h1>FortiManager API Endpoint Test Results</h1>
    {% for result in results %}
    <h2>{{ result.url }}</h2>
    {% if result.get('error') %}
    <p>Error: {{ result.error }}</p>
    {% else %}
    <p>Status Code: {{ result.status_code }}</p>
    <p>Message: {{ result.message }}</p>
    <pre>{{ result.response | tojson(indent=2) }}</pre>
    {% endif %}
    <hr>
    {% endfor %}
    <a href="{{ url_for('index') }}">Back to Home</a>
    """, results=results)

@app.route('/check_token', methods=['GET'])
def check_token():
    """Endpoint to check the status of the session token."""
    logger.info("Received request to /check_token")
    query_payload = {
        "method": "exec",
        "params": [
            {
                "url": "/sys/status"
            }
        ],
        "session": session_token,
        "id": 1
    }
    try:
        logger.info(f"Sending request to FortiManager: {FMGR_URL}")
        logger.info(f"Request payload: {json.dumps(query_payload, indent=2)}")
        response = requests.post(FMGR_URL, json=query_payload, verify=SSL_VERIFY)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        logger.info(f"Response content: {response.text}")
        response.raise_for_status()
        json_response = response.json()
        logger.info(f"Token check response: {json.dumps(json_response, indent=2)}")
        return render_template_string("""
        <h1>Session Token Status</h1>
        <pre>{{ response }}</pre>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, response=json.dumps(json_response, indent=2))
    except Exception as e:
        logger.error(f"Error in check_token: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return render_template_string("""
        <h1>Session Token Check Error</h1>
        <p>{{ error }}</p>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, error=str(e))

@app.route('/user_info', methods=['GET'])
def user_info():
    """Endpoint to retrieve current user information."""
    logger.info("Received request to /user_info")
    query_payload = {
        "method": "get",
        "params": [
            {
                "url": "/sys/admin/user"
            }
        ],
        "session": session_token,
        "id": 1
    }
    try:
        response = requests.post(FMGR_URL, json=query_payload, verify=SSL_VERIFY)
        response.raise_for_status()
        json_response = response.json()
        logger.info(f"User info response: {json.dumps(json_response, indent=2)}")
        return render_template_string("""
        <h1>Current User Information</h1>
        <pre>{{ response }}</pre>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, response=json.dumps(json_response, indent=2))
    except Exception as e:
        logger.error(f"Error in user_info: {str(e)}")
        return render_template_string("""
        <h1>User Info Error</h1>
        <p>{{ error }}</p>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, error=str(e))

if __name__ == '__main__':
    init_db()
    session_token = get_session_token()
    if session_token is None:
        logger.error("Failed to obtain initial session token. Exiting.")
        sys.exit(1)
    app.run(debug=DEBUG, host=HOST, port=PORT, use_reloader=False)
