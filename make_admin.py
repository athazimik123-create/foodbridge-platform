# ============================================================
# make_admin.py — Secure Admin Promotion Script
# ============================================================
# Run this script from your terminal to securely promote any 
# registered user to the Admin role.
#
# Usage:
#   python make_admin.py your_email@example.com
# ============================================================

import sys
from dotenv import load_dotenv
load_dotenv()

from firebase_config import _init_firebase, get_db

_init_firebase()
db = get_db()

def make_admin(email: str):
    if not db:
        print("❌ Error: Not connected to Live Firebase Database.")
        return

    # Find the user by email in the users collection
    users_ref = db.collection("users").where("email", "==", email).stream()
    
    user_doc = None
    for doc in users_ref:
        user_doc = doc
        break
        
    if not user_doc:
        print(f"❌ Error: No user found with the email '{email}'.")
        print("   Make sure you register an account on the website first!")
        return
        
    # Update the user's role
    user_id = user_doc.id
    db.collection("users").document(user_id).update({"role": "admin"})
    
    print(f"✅ Success! User '{email}' has been promoted to Admin.")
    print(f"   They can now refresh the website and they will see the Admin dashboard.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <user_email>")
    else:
        make_admin(sys.argv[1])
