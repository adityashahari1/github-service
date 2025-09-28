# Logging utilities
# Author: Mohsen Minai

import json
import logging
from datetime import datetime


class Logger:
    #logger that outputs JSOn
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_request(self, method, path, **extra):
        #Log HTTP requests
        data = {
            "time": datetime.utcnow().isoformat(),
            "type": "request",
            "method": method,
            "path": path,
            **extra
        }
        self.logger.info(json.dumps(data))
    
    def log_github_call(self, method, url, status_code):
    #log GitHub API calls
        data = {
            "time": datetime.utcnow().isoformat(),
            "type": "github_api",
            "method": method,
            "url": url,
            "status": status_code
        }
        self.logger.info(json.dumps(data))
    
    def log_webhook(self, delivery_id, event_type, action):
        #log webhook events#
        data = {
            "time": datetime.utcnow().isoformat(),
            "type": "webhook",
            "delivery_id": delivery_id,
            "event": event_type,
            "action": action
        }
        self.logger.info(json.dumps(data))
    
    def log_error(self, message, **extra):
        #Log errors
        data = {
            "time": datetime.utcnow().isoformat(),
            "type": "error",
            "message": message,
            **extra
        }
        self.logger.error(json.dumps(data))
    
    def info(self, message, *args):
        #Standard info logging for compatibility
        if args:
            message = message % args
        self.logger.info(message)
    
    def error(self, message, *args):
        #Standard error logging for compatibility
        if args:
            message = message % args
        self.logger.error(message)


# global logger
logger = Logger(__name__)


