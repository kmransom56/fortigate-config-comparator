import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FortiManager URL
FMGR_URL = os.getenv('FMGR_URL', 'https://10.128.144.132:443/jsonrpc')

# FortiManager credentials
FMGR_USERNAME = os.getenv('FMGR_USERNAME')
FMGR_PASSWORD = os.getenv('FMGR_PASSWORD')

# Database configuration
DB_NAME = os.getenv('DB_NAME', 'fortigate_ips.db')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'app.log')

# Flask configuration
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))

# SSL Verification
SSL_VERIFY = os.getenv('SSL_VERIFY', 'True').lower() in ('true', '1', 't')

# Log all environment variables (excluding any sensitive information)
logger.info("Environment variables:")
for key, value in os.environ.items():
    if 'password' in key.lower() or 'secret' in key.lower():
        logger.info(f"{key}: [REDACTED]")
    else:
        logger.info(f"{key}: {value}")

# Validate required environment variables
if not FMGR_USERNAME or not FMGR_PASSWORD:
    raise ValueError("FMGR_USERNAME and FMGR_PASSWORD environment variables must be set")
