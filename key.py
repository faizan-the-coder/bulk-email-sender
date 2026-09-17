from cryptography.fernet import Fernet
import datetime
import os

# Demo licensing-key generator. Set EMAIL_APP_FERNET_KEY to reuse a stable key;
# otherwise an ephemeral demo key is generated (keys won't verify across runs).
FERNET_KEY_RAW = os.environ.get("EMAIL_APP_FERNET_KEY") or Fernet.generate_key().decode()
SECRET_KEY = FERNET_KEY_RAW.encode()  # demo only - never commit a real key
cipher = Fernet(SECRET_KEY)

expiry = datetime.datetime(2025, 11, 4, 10, 5, 0)  # set client expiry date & time
encrypted_key = cipher.encrypt(expiry.strftime("%Y-%m-%d %H:%M:%S").encode())

print("Give this key to client:")
print(encrypted_key.decode())
