from utils.db import test_connection

if test_connection():
    print("SUCCESS: Connected to Neon")
else:
    print("FAILED: Connection failed")