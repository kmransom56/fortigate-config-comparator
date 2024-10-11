import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# FortiManager URL
FMGR_URL = os.getenv('FMGR_URL', 'https://10.128.144.132:443/jsonrpc')

# FortiManager credentials
FMGR_USERNAME = os.getenv('FMGR_USERNAME')
FMGR_PASSWORD = os.getenv('FMGR_PASSWORD')



# Database configuration
DB_NAME = os.getenv('DB_NAME', 'fortigate_ips.db')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', './app.log')

# Ensure the log directory exists
log_file_path = os.path.abspath(LOG_FILE)
log_directory = os.path.dirname(log_file_path)
if log_directory and not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler
file_handler = RotatingFileHandler(log_file_path, maxBytes=10*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(LOG_LEVEL)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(LOG_LEVEL)

# Get the root logger
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# Now load SSL_VERIFY
SSL_VERIFY = os.getenv('SSL_VERIFY', 'False').lower() == 'true'
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