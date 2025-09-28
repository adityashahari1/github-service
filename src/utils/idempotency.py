# Idempotency handling
# Author: Mohsen Minai

import hashlib
from datetime import datetime


class idempotency:
#track processed webhooks to avoid duplicates
    
    def __init__(self):
        self.processed = set()  # store processed webhook IDs
        self.events = []        # store event details for events endpoint
    
    def make_unique_id(self, delivery_id, event_type, action):
       
        combined = f"{delivery_id}:{event_type}:{action}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def already_processed(self, delivery_id, event_type, action):
        unique_id = self.make_unique_id(delivery_id, event_type, action)
        return unique_id in self.processed
    
    def mark_processed(self, delivery_id, event_type, action, payload):
        
        unique_id = self.make_unique_id(delivery_id, event_type, action)
        self.processed.add(unique_id)
        
        #store details for events endpoint
        event_info = {
            "delivery_id": delivery_id,
            "event": event_type,
            "action": action,
            "time": datetime.utcnow().isoformat(),
            "issue_number": payload.get("issue", {}).get("number") if "issue" in payload else None
        }
        self.events.append(event_info)
        

        if len(self.events) > 100:
            self.events = self.events[-100:]
    
    def get_recent_events(self, limit=50):
    #get recent webhook events
        return self.events[-limit:]



idempotency = idempotency()


