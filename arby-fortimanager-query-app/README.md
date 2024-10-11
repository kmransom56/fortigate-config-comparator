# FortiManager Query App

This Flask application queries a FortiManager for VLAN 10 IPs of managed FortiGate devices, stores the information in a SQLite database, and provides endpoints to fetch and retrieve this data.

## Features

- Fetch VLAN 10 IPs from FortiManager
- Store IP information in a SQLite database
- Retrieve stored IP information
- Configurable through environment variables
- Logging to both file and console

## Prerequisites

- Python 3.7+
- pip (Python package manager)
- Access to a FortiManager instance

## Installation and Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/fortimanager-query-app.git
   cd fortimanager-query-app
   ```

2. Run the setup script:
   
   For Unix-based systems (Linux, macOS):
   ```
   chmod +x setup.sh
   ./setup.sh
   ```

   For Windows:
   ```
   setup.bat
   ```

   This script will:
   - Create and activate a virtual environment
   - Install the required packages
   - Create a `.env` file from `.env.example` if it doesn't exist
   - Run the application

3. If the `.env` file was just created, edit it with your FortiManager details before running the application.

## Configuration

The application is configured using environment variables. The setup script creates a `.env` file from `.env.example`. Edit the `.env` file and adjust the values as needed:

```
FMGR_URL=https://your-fortimanager-url/jsonrpc
FMGR_API_TOKEN=your-api-token
DB_NAME=fortigate_ips.db
LOG_LEVEL=INFO
LOG_FILE=app.log
DEBUG=False
HOST=0.0.0.0
PORT=5000
SSL_VERIFY=True
```

## Running the Application

If you've used the setup script, the application should already be running. If you need to run it again:

1. Ensure you're in the project directory and your virtual environment is activated.

2. Run the Flask application:
   ```
   python app.py
   ```

3. The application will be available at `http://localhost:5000` (or the host/port you configured).

## Using the API

The application provides the following API endpoints:

### 1. Fetch VLAN 10 IPs from FortiManager

To fetch the VLAN 10 IPs from FortiManager and store them in the local database:

```
curl -X POST http://localhost:5000/fetch_ips
```

This will query the FortiManager for all managed devices, find their VLAN 10 interfaces, and store the IP addresses in the local database.

### 2. Retrieve stored VLAN 10 IPs

To retrieve the stored VLAN 10 IPs:

```
curl http://localhost:5000/get_ips
```

This will return a JSON array of objects, each containing a device name and its VLAN 10 IP address.

### 3. Test the API

To test if the API is running:

```
curl http://localhost:5000/test
```

## Workflow to Get VLAN 10 IP Addresses

1. First, run the fetch_ips endpoint to query the FortiManager and update the local database:
   ```
   curl -X POST http://localhost:5000/fetch_ips
   ```
   This step is crucial and must be performed before attempting to retrieve the IP addresses.

2. Then, retrieve the stored IP addresses:
   ```
   curl http://localhost:5000/get_ips
   ```

3. The response will be a JSON array of objects, each containing a device name and its VLAN 10 IP address, for example:
   ```json
   [
     {"device_name": "FortiGate1", "ip_address": "10.0.10.1"},
     {"device_name": "FortiGate2", "ip_address": "10.0.10.2"},
     ...
   ]
   ```

   If no data has been fetched yet, you'll receive a message indicating that you need to run the /fetch_ips endpoint first.

## Troubleshooting

- If you receive an empty array `[]` when calling `/get_ips`, it means that no data has been fetched from the FortiManager yet. Make sure to call the `/fetch_ips` endpoint first.
- If you encounter any errors, check the `app.log` file for detailed error messages and stack traces.
- Ensure that your FortiManager URL and API token are correctly set in the `.env` file.
- If SSL verification is failing, you can set `SSL_VERIFY=False` in the `.env` file, but this is not recommended for production use.

## Running Tests

To run the test suite:

```
pytest test_app.py
```

## Logging

Logs are written to both the console and a log file (default: `app.log`). The log level and file location can be configured using environment variables.

## Security Considerations

- Always use environment variables to store sensitive information like API tokens.
- In a production environment, ensure SSL verification is enabled (`SSL_VERIFY=True`).
- Review and adjust the error messages to ensure they don't reveal sensitive information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
