import hashlib
import hmac

secret = 'supersecret'


def encode_username(username):
   sig = hmac.new(secret.encode(), username.encode(), hashlib.sha256).hexdigest()
   return f"{username}.{sig}"


def decode_token(token):
   try:
      username, sig = token.split('.')
      expected_sig = hmac.new(secret.encode(), username.encode(), hashlib.sha256).hexdigest()
      if hmac.compare_digest(sig, expected_sig):
         return username
   except ValueError:
      pass
   return None
