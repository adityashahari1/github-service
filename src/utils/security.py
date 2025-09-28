# Webhook signature verification
# Author: Mohsen Minai

import hmac
import hashlib


def verify_webhook_signature(payload_bytes, signature, secret):
#check if webhook signature is valid
    if not signature or not signature.startswith('sha256='):
        return False
    
    #remove "sha256=" from start
    expected_hash = signature[7:]
    
    #calculate what the hash should be
    secret_bytes = secret.encode('utf-8')
    calculated_hash = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()
    
    #compare safely
    return hmac.compare_digest(expected_hash, calculated_hash)




