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
    requests.packages.urllib3.disable_warnings()
    
# Create Flask app instance    
app = Flask(__name__)
# Define the get_session_token function
def get_session_token():
    try:
        # Simulate obtaining a session token
        session_token = "dummy_session_token"
        return session_token
    except Exception as e:
        logger.error(f"Failed to get session token: {str(e)}")
        return None
# Function to get headers with token
def get_headers():
    return {
        'Authorization': f'Bearer {FMGR_TOKEN}',
        'Content-Type': 'application/json'
    }
# Example function to make a request to FortiManager
def get_fmgr_data(endpoint):
    url = f"{FMGR_URL}/{endpoint}"
    headers = get_headers()
    response = requests.get(url, headers=headers, verify=SSL_VERIFY)
    return response.json()
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
    global session_token
    logger.info("Starting fetch_vlan_10_ips function")
    
    try:
        # Query for FortiGate devices
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
        logger.info(f"Sending request to FortiManager: {FMGR_URL}")
        logger.info(f"Request payload: {json.dumps(query_payload, indent=2)}")
        response = requests.post(FMGR_URL, json=query_payload, verify=SSL_VERIFY)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        logger.info(f"Response content: {response.text}")

        response.raise_for_status()
        
        json_response = response.json()
        logger.info(f"Full API response: {json.dumps(json_response, indent=2)}")
        
        # Check for API-level errors
        if 'result' in json_response and isinstance(json_response['result'], list) and len(json_response['result']) > 0:
            result = json_response['result'][0]
            if 'status' in result and 'code' in result['status']:
                status_code = result['status']['code']
                status_message = result['status'].get('message', 'Unknown error')
                if status_code != 0:  # Non-zero status code indicates an error
                    if status_code == -11:
                        logger.error("Session token expired. Refreshing token.")
                        refresh_session_token()
                        return fetch_vlan_10_ips()  # Retry with new token
                    logger.error(f"API returned an error. Code: {status_code}, Message: {status_message}")
                    if status_code == -11:
                        return f"Error: No permission for the resource. Please check your credentials.", 403
                    return f"Error from FortiManager API: {status_message} (Code: {status_code})", 400

        devices = json_response.get('result', [])[0].get('data', [])
        logger.info(f"Received {len(devices)} devices from FortiManager")
        
        if not devices:
            logger.warning("No devices returned from FortiManager")
            return "No devices found in FortiManager. Please check your permissions and FortiManager configuration.", 404

        vlan_10_ips = {}
        for device in devices:
            dev_name = device['name']
            logger.info(f"Querying interfaces for device: {dev_name}")
            dev_query_payload = {
                "method": "get",
                "params": [
                    {
                        "url": f"/pm/config/device/{dev_name}/global/system/interface"
                    }
                ],
                "session": session_token,
                "id": 2
            }
            response = requests.post(FMGR_URL, json=dev_query_payload, verify=SSL_VERIFY)
            logger.info(f"Response status code for {dev_name}: {response.status_code}")
            logger.info(f"Response content for {dev_name}: {response.text}")
            response.raise_for_status()
            interfaces = response.json().get('result', [])[0].get('data', [])
            logger.info(f"Received {len(interfaces)} interfaces for device {dev_name}")
            for interface in interfaces:
                if interface.get('vlanid') == 10:
                    vlan_10_ips[dev_name] = interface.get('ip')
                    logger.info(f"Found VLAN 10 IP for {dev_name}: {interface.get('ip')}")

        logger.info(f"VLAN 10 IPs found: {vlan_10_ips}")

        if not vlan_10_ips:
            logger.warning("No VLAN 10 IPs found for any device")
            return "No VLAN 10 IPs found for any device", 404

        # Store in database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM vlan10_ips")
        for dev_name, ip in vlan_10_ips.items():
            c.execute("INSERT INTO vlan10_ips (device_name, ip_address) VALUES (?, ?)", (dev_name, ip))
        conn.commit()
        conn.close()
        logger.info("Data stored in database successfully")

        return f"Data fetched and stored successfully. Found {len(vlan_10_ips)} VLAN 10 IPs.", 200
    except requests.RequestException as e:
        logger.error(f"Error fetching data from FortiManager: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error fetching data from FortiManager: {str(e)}", 500
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Database error: {str(e)}", 500
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Error decoding JSON response: {str(e)}", 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Unexpected error: {str(e)}", 500

@app.route('/')
def index():
    """Render the index page with buttons to fetch and retrieve IPs."""
    logger.info("Received request to /")
    ssl_warning = "WARNING: SSL verification is disabled. This is not recommended for production use." if not SSL_VERIFY else ""
    return render_template_string("""
    <h1>FortiManager Query App</h1>
    <p style="color: red; font-weight: bold;">{{ ssl_warning }}</p>
    <form action="{{ url_for('fetch_ips') }}" method="post">
        <input type="submit" value="Fetch VLAN 10 IPs">
    </form>
    <br>
    <form action="{{ url_for('get_ips') }}" method="get">
        <input type="submit" value="Retrieve VLAN 10 IPs">
    </form>
    <br>
    <a href="{{ url_for('debug_api') }}">Debug API Response</a>
    <br>
    <a href="{{ url_for('debug_api_full') }}">Debug API Response (Full)</a>
    <br>
    <a href="{{ url_for('test_endpoints') }}">Test API Endpoints</a>
    <br>
    <a href="{{ url_for('check_token') }}">Check Session Token</a>
    <br>
    <a href="{{ url_for('user_info') }}">Get User Info</a>
    """, ssl_warning=ssl_warning)

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
    """Endpoint to retrieve stored VLAN 10 IPs."""
    logger.info("Received request to /get_ips")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT device_name, ip_address FROM vlan10_ips")
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        logger.info(f"Retrieved IPs from database: {rows}")
        if not rows:
            message = 'No VLAN 10 IPs found. Please fetch IPs first.'
            return render_template_string("""
            <h1>VLAN 10 IPs</h1>
            <p>{{ message }}</p>
            <a href="{{ url_for('index') }}">Back to Home</a>
            """, message=message)
        return render_template_string("""
        <h1>VLAN 10 IPs</h1>
        <table border="1">
            <tr>
                <th>Device Name</th>
                <th>IP Address</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row['device_name'] }}</td>
                <td>{{ row['ip_address'] }}</td>
            </tr>
            {% endfor %}
        </table>
        <br>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, rows=rows)
    except sqlite3.Error as e:
        logger.error(f"Database error in get_ips: {str(e)}")
        return render_template_string("""
        <h1>Error</h1>
        <p>Database error: {{ error }}</p>
        <a href="{{ url_for('index') }}">Back to Home</a>
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
        "id": 1
    }
    try:
        headers = get_headers()
        response = requests.post(FMGR_URL, json=query_payload, headers=headers, verify=SSL_VERIFY)
        response.raise_for_status()
        json_response = response.json()
        logger.info(f"Debug API response: {json.dumps(json_response, indent=2)}")
        return render_template_string("""
        <h1>Debug API Response</h1>
        <pre>{{ response }}</pre>
        <a href="{{ url_for('index') }}">Back to Home</a>
        """, response=json.dumps(json_response, indent=2))
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
        "id": 1
    }
    try:
        headers = get_headers()
        logger.info(f"Sending request to FortiManager: {FMGR_URL}")
        logger.info(f"Request payload: {json.dumps(query_payload, indent=2)}")
        response = requests.post(FMGR_URL, json=query_payload, headers=headers, verify=SSL_VERIFY)
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
            "id": 1
        }
        try:
            headers = get_headers()
            logger.info(f"Testing endpoint: {url}")
            response = requests.post(FMGR_URL, json=query_payload, headers=headers, verify=SSL_VERIFY)
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
        "id": 1
    }
    try:
        headers = get_headers()
        logger.info(f"Sending request to FortiManager: {FMGR_URL}")
        logger.info(f"Request payload: {json.dumps(query_payload, indent=2)}")
        response = requests.post(FMGR_URL, json=query_payload, headers=headers, verify=SSL_VERIFY)
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
        "id": 1
    }
    try:
        headers = get_headers()
        response = requests.post(FMGR_URL, json=query_payload, headers=headers, verify=SSL_VERIFY)
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
