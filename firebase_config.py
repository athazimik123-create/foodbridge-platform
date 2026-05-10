# ============================================================
# firebase_config.py — FoodBridge Firebase Integration
# ============================================================
# Handles Firebase Admin SDK init, Auth REST API calls,
# and all Firestore CRUD helpers.
#
# SETUP:
#   1. Place serviceAccountKey.json in the project root
#   2. Copy .env.example → .env and fill in values
# ============================================================

import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

load_dotenv()

# ── Helper: env / secrets ────────────────────────────────────
def _env(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


SERVICE_ACCOUNT_PATH = _env("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")
PROJECT_ID           = _env("FIREBASE_PROJECT_ID", "foodbridge-demo")
FIREBASE_WEB_API_KEY = _env("FIREBASE_WEB_API_KEY", "DEMO_KEY")
GOOGLE_MAPS_API_KEY  = _env("GOOGLE_MAPS_API_KEY", "")

# ── Firebase init (singleton) ────────────────────────────────
def _init_firebase():
    if firebase_admin._apps:
        return
    # 1. Streamlit secrets JSON
    try:
        import streamlit as st
        if "FIREBASE_SERVICE_ACCOUNT_JSON" in st.secrets:
            raw = st.secrets["FIREBASE_SERVICE_ACCOUNT_JSON"]
            cred_dict = dict(raw) if not isinstance(raw, str) else json.loads(raw)
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
            return
    except Exception:
        pass
    # 2. Env-var JSON
    json_env = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if json_env:
        try:
            cred_dict = json.loads(json_env)
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
            return
        except Exception as e:
            print(f"[Firebase] JSON env error: {e}")
    # 3. File
    if os.path.exists(SERVICE_ACCOUNT_PATH):
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {"projectId": PROJECT_ID})
        print("[Firebase] Initialized from file.")
    else:
        print("[Firebase] MOCK MODE — no credentials found.")


_init_firebase()


def get_db():
    try:
        return firestore.client()
    except Exception:
        return None


db = get_db()

# ── Firebase Auth REST ────────────────────────────────────────
import requests as _req

_SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={k}"
_SIGN_UP_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={k}"


def sign_in(email: str, password: str) -> dict:
    if FIREBASE_WEB_API_KEY == "DEMO_KEY":
        # MOCK AUTH
        _mu = {
            "admin@foodbridge.com":    {"role": "admin",    "name": "Admin Alex"},
            "donor@foodbridge.com":    {"role": "donor",    "name": "Diana Donor"},
            "receiver@foodbridge.com": {"role": "receiver", "name": "Rachel NGO"},
        }
        if email in _mu and password == "demo1234":
            uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
            return {"idToken": f"MOCK_{uid}", "localId": uid, **_mu[email], "email": email}
        return {"error": "Invalid credentials (mock mode — use demo1234)"}

    try:
        resp = _req.post(_SIGN_IN_URL.format(k=FIREBASE_WEB_API_KEY),
                         json={"email": email, "password": password, "returnSecureToken": True},
                         timeout=10)
        data = resp.json()
        if "idToken" not in data:
            return {"error": data.get("error", {}).get("message", "Auth failed")}
        profile = get_user(data["localId"]) or {}
        data["role"] = profile.get("role", "receiver")
        data["name"] = profile.get("name", email.split("@")[0])
        return data
    except Exception as e:
        return {"error": str(e)}


def sign_up(email: str, password: str, name: str, role: str) -> dict:
    if FIREBASE_WEB_API_KEY == "DEMO_KEY":
        return {"error": "Sign-up requires real Firebase credentials."}
    try:
        resp = _req.post(_SIGN_UP_URL.format(k=FIREBASE_WEB_API_KEY),
                         json={"email": email, "password": password, "returnSecureToken": True},
                         timeout=10)
        data = resp.json()
        if "idToken" not in data:
            return {"error": data.get("error", {}).get("message", "Registration failed")}
        uid = data["localId"]
        create_user_profile(uid, {
            "uid": uid, "name": name, "email": email, "role": role,
            "subscription_tier": "basic", "created_at": datetime.now(timezone.utc),
            "location": None, "address": "",
        })
        data["role"] = role
        data["name"] = name
        return data
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════
# USERS
# ════════════════════════════════════════════════════════════

def create_user_profile(uid: str, profile: dict):
    if db:
        db.collection("users").document(uid).set(profile)
    else:
        _MOCK_USERS[uid] = profile


def get_user(uid: str) -> dict | None:
    if db:
        doc = db.collection("users").document(uid).get()
        return doc.to_dict() if doc.exists else None
    return _MOCK_USERS.get(uid)


def get_all_users() -> List[dict]:
    if db:
        docs = db.collection("users").stream()
        return [d.to_dict() for d in docs]
    return list(_MOCK_USERS.values())


# ════════════════════════════════════════════════════════════
# FOOD LISTINGS  (donor → Firestore → receivers see live)
# ════════════════════════════════════════════════════════════

def create_food_listing(data: dict) -> str:
    listing_id = str(uuid.uuid4())
    doc = {
        "listing_id":   listing_id,
        "donor_id":     data.get("donor_id"),
        "donor_name":   data.get("donor_name", "Anonymous"),
        "food_name":    data.get("food_name"),
        "food_type":    data.get("food_type", "Mixed"),
        "quantity_kg":  float(data.get("quantity_kg", 0)),
        "servings":     int(data.get("servings", 0)),
        "description":  data.get("description", ""),
        "address":      data.get("address", ""),
        "lat":          data.get("lat", 0.0),
        "lng":          data.get("lng", 0.0),
        "expiry_dt":    data.get("expiry_dt"),
        "status":       data.get("status", "available"),  # available | requested | in_transit | delivered | disposed
        "receiver_id":  None,
        "driver_id":    None,
        "created_at":   datetime.now(timezone.utc),
        "pickup_window": data.get("pickup_window", "Flexible"),
        "tags":          data.get("tags", []),
        "revenue_generated": 0.0,
        "premium_pickup": data.get("premium_pickup", False),
    }
    if db:
        db.collection("food_listings").document(listing_id).set(doc)
    else:
        _MOCK_LISTINGS.append(doc)
        
    # If the listing is available, we might want to notify receivers.
    # In a real app, this might trigger a push notification. We'll store it in DB.
    if doc["status"] == "available":
        create_platform_notification(
            title="New Food Listed! 🥗",
            message=f"{doc['donor_name']} listed {doc['quantity_kg']}kg of {doc['food_name']}.",
            n_type="new_listing"
        )
        
    return listing_id


def get_available_listings(limit: int = 60) -> List[dict]:
    if db:
        docs = (
            db.collection("food_listings")
            .where("status", "==", "available")
            .limit(limit)
            .stream()
        )
        results = [d.to_dict() for d in docs]
        results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return results
    return [l for l in _MOCK_LISTINGS if l["status"] == "available"]


def get_all_listings(limit: int = 100) -> List[dict]:
    if db:
        docs = db.collection("food_listings").limit(limit).stream()
        results = [d.to_dict() for d in docs]
        results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return results
    return list(_MOCK_LISTINGS)


def get_donor_listings(donor_id: str) -> List[dict]:
    if db:
        docs = db.collection("food_listings").where("donor_id", "==", donor_id).stream()
        results = [d.to_dict() for d in docs]
        results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return results
    return [l for l in _MOCK_LISTINGS if l.get("donor_id") == donor_id]


def request_food(listing_id: str, receiver_id: str, premium: bool = False) -> None:
    update = {
        "receiver_id": receiver_id,
        "status":      "requested",
        "requested_at": datetime.now(timezone.utc),
        "premium_pickup": premium,
        "revenue_generated": 4.99 if premium else 0.0,
    }
    if db:
        db.collection("food_listings").document(listing_id).update(update)
    else:
        for l in _MOCK_LISTINGS:
            if l["listing_id"] == listing_id:
                l.update(update)
                break


def update_listing_status(listing_id: str, status: str) -> None:
    update = {"status": status, "updated_at": datetime.now(timezone.utc)}
    if db:
        db.collection("food_listings").document(listing_id).update(update)
    else:
        for l in _MOCK_LISTINGS:
            if l["listing_id"] == listing_id:
                l.update(update)
                break


def update_food_listing(listing_id: str, fields: dict) -> None:
    """Patch editable fields on a food listing (donor corrections)."""
    fields["updated_at"] = datetime.now(timezone.utc)
    if db:
        db.collection("food_listings").document(listing_id).update(fields)
    else:
        for l in _MOCK_LISTINGS:
            if l["listing_id"] == listing_id:
                l.update(fields)
                break


def delete_food_listing(listing_id: str) -> None:
    """Hard-delete a food listing from Firestore (or mock store)."""
    if db:
        db.collection("food_listings").document(listing_id).delete()
    else:
        global _MOCK_LISTINGS
        _MOCK_LISTINGS = [l for l in _MOCK_LISTINGS if l["listing_id"] != listing_id]


def get_receiver_requests(receiver_id: str) -> List[dict]:

    if db:
        docs = db.collection("food_listings").where("receiver_id", "==", receiver_id).stream()
        results = [d.to_dict() for d in docs]
        results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return results
    return [l for l in _MOCK_LISTINGS if l.get("receiver_id") == receiver_id]


# ════════════════════════════════════════════════════════════
# TRANSACTIONS
# ════════════════════════════════════════════════════════════

def log_transaction(user_id: str, amount: float, tx_type: str, meta: dict = None) -> str:
    tx_id = str(uuid.uuid4())
    doc = {
        "tx_id":     tx_id,
        "user_id":   user_id,
        "amount":    amount,
        "type":      tx_type,
        "meta":      meta or {},
        "timestamp": datetime.now(timezone.utc),
    }
    if db:
        db.collection("transactions").document(tx_id).set(doc)
    else:
        _MOCK_TRANSACTIONS.append(doc)
    return tx_id


def get_all_transactions(limit: int = 200) -> List[dict]:
    if db:
        docs = (
            db.collection("transactions")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        return [d.to_dict() for d in docs]
    return sorted(_MOCK_TRANSACTIONS, key=lambda x: x.get("timestamp") or "", reverse=True)


# ════════════════════════════════════════════════════════════
# DELIVERY ROUTES  (route optimizer data)
# ════════════════════════════════════════════════════════════

def save_route(route_data: dict) -> str:
    route_id = str(uuid.uuid4())
    doc = {
        "route_id":     route_id,
        "driver_id":    route_data.get("driver_id"),
        "listing_ids":  route_data.get("listing_ids", []),
        "waypoints":    route_data.get("waypoints", []),
        "total_km":     route_data.get("total_km", 0),
        "est_minutes":  route_data.get("est_minutes", 0),
        "status":       "planned",   # planned | active | completed
        "created_at":   datetime.now(timezone.utc),
    }
    if db:
        db.collection("routes").document(route_id).set(doc)
    else:
        _MOCK_ROUTES.append(doc)
    return route_id


def get_routes(limit: int = 20) -> List[dict]:
    if db:
        docs = db.collection("routes").limit(limit).stream()
        return [d.to_dict() for d in docs]
    return _MOCK_ROUTES


# ════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ════════════════════════════════════════════════════════════

def get_platform_stats() -> dict:
    listings = get_all_listings(500)
    txs = get_all_transactions(500)

    total_kg = sum(l.get("quantity_kg", 0) for l in listings)
    delivered = [l for l in listings if l.get("status") == "delivered"]
    pending   = [l for l in listings if l.get("status") == "available"]
    requested = [l for l in listings if l.get("status") in ("requested", "in_transit")]

    rev_logistics = sum(t["amount"] for t in txs if t["type"] == "logistics_fee")
    rev_sub       = sum(t["amount"] for t in txs if t["type"] == "subscription")
    rev_csr       = sum(t["amount"] for t in txs if t["type"] == "csr_credit")

    return {
        "total_listings":   len(listings),
        "available":        len(pending),
        "requested":        len(requested),
        "delivered":        len(delivered),
        "total_kg":         round(total_kg, 1),
        "meals_saved":      int(total_kg * 2.5),
        "co2_offset_kg":    round(total_kg * 2.1, 1),
        "total_users":      len(get_all_users()),
        "total_revenue":    round(rev_logistics + rev_sub + rev_csr, 2),
        "logistics_rev":    round(rev_logistics, 2),
        "sub_rev":          round(rev_sub, 2),
        "csr_rev":          round(rev_csr, 2),
    }


# ════════════════════════════════════════════════════════════
# IN-MEMORY MOCK DATA
# ════════════════════════════════════════════════════════════

def _uid(email): return str(uuid.uuid5(uuid.NAMESPACE_DNS, email))

_MOCK_USERS = {
    _uid("admin@foodbridge.com"):    {"uid": _uid("admin@foodbridge.com"),    "name": "Admin Alex",   "email": "admin@foodbridge.com",    "role": "admin",    "subscription_tier": "pro"},
    _uid("donor@foodbridge.com"):    {"uid": _uid("donor@foodbridge.com"),    "name": "Diana Donor",  "email": "donor@foodbridge.com",    "role": "donor",    "subscription_tier": "basic"},
    _uid("receiver@foodbridge.com"): {"uid": _uid("receiver@foodbridge.com"), "name": "Rachel NGO",   "email": "receiver@foodbridge.com", "role": "receiver", "subscription_tier": "basic"},
}

_now = datetime.now(timezone.utc)

_MOCK_LISTINGS = [
    {"listing_id": "lst-001", "donor_id": _uid("donor@foodbridge.com"), "donor_name": "Diana Donor",
     "food_name": "Fresh Bread & Pastries", "food_type": "Bakery", "quantity_kg": 12.5, "servings": 50,
     "description": "End-of-day bread, muffins and croissants from our bakery. Still fresh!", "address": "123 Main St, Mumbai",
     "lat": 19.0760, "lng": 72.8777, "expiry_dt": (_now + timedelta(hours=6)).isoformat(),
     "status": "available", "receiver_id": None, "driver_id": None, "created_at": _now - timedelta(hours=1),
     "pickup_window": "5pm–7pm", "tags": ["veg", "bakery"], "revenue_generated": 0.0, "premium_pickup": False},
    {"listing_id": "lst-002", "donor_id": _uid("donor@foodbridge.com"), "donor_name": "Diana Donor",
     "food_name": "Cooked Rice & Dal", "food_type": "Prepared Meals", "quantity_kg": 30.0, "servings": 120,
     "description": "Hot prepared meals from wedding catering event. Serves ~120 people.", "address": "Hotel Grand, Delhi",
     "lat": 28.6139, "lng": 77.2090, "expiry_dt": (_now + timedelta(hours=3)).isoformat(),
     "status": "available", "receiver_id": None, "driver_id": None, "created_at": _now - timedelta(minutes=30),
     "pickup_window": "4pm–5pm", "tags": ["veg", "hot-food"], "revenue_generated": 0.0, "premium_pickup": False},
    {"listing_id": "lst-003", "donor_id": _uid("donor@foodbridge.com"), "donor_name": "Diana Donor",
     "food_name": "Mixed Vegetables", "food_type": "Produce", "quantity_kg": 20.0, "servings": 80,
     "description": "Seasonal vegetables from supermarket. Slightly cosmetically imperfect but fully edible.", "address": "Supermart Navi Mumbai",
     "lat": 19.0330, "lng": 73.0297, "expiry_dt": (_now + timedelta(days=2)).isoformat(),
     "status": "requested", "receiver_id": _uid("receiver@foodbridge.com"), "driver_id": None,
     "created_at": _now - timedelta(hours=4), "pickup_window": "Anytime", "tags": ["veg", "produce"],
     "revenue_generated": 4.99, "premium_pickup": True},
    {"listing_id": "lst-004", "donor_id": _uid("donor@foodbridge.com"), "donor_name": "Diana Donor",
     "food_name": "Packaged Dairy Items", "food_type": "Dairy", "quantity_kg": 8.0, "servings": 40,
     "description": "Yogurt, milk and cheese nearing best-before date — still perfectly safe.", "address": "City Dairy Pune",
     "lat": 18.5204, "lng": 73.8567, "expiry_dt": (_now + timedelta(days=1)).isoformat(),
     "status": "delivered", "receiver_id": _uid("receiver@foodbridge.com"), "driver_id": None,
     "created_at": _now - timedelta(days=1), "pickup_window": "Morning", "tags": ["dairy", "packaged"],
     "revenue_generated": 0.0, "premium_pickup": False},
]

_MOCK_TRANSACTIONS = [
    {"tx_id": "tx-001", "user_id": _uid("donor@foodbridge.com"),    "amount": 29.0,  "type": "subscription",  "meta": {"tier": "pro"},         "timestamp": _now - timedelta(days=30)},
    {"tx_id": "tx-002", "user_id": _uid("receiver@foodbridge.com"), "amount": 4.99,  "type": "logistics_fee", "meta": {"listing_id": "lst-003"},"timestamp": _now - timedelta(hours=4)},
    {"tx_id": "tx-003", "user_id": "csr-001",                       "amount": 500.0, "type": "csr_credit",    "meta": {"credits": 5000},        "timestamp": _now - timedelta(days=5)},
    {"tx_id": "tx-004", "user_id": _uid("donor@foodbridge.com"),    "amount": 29.0,  "type": "subscription",  "meta": {"tier": "pro"},         "timestamp": _now - timedelta(days=60)},
    {"tx_id": "tx-005", "user_id": "csr-002",                       "amount": 200.0, "type": "csr_credit",    "meta": {"credits": 2000},        "timestamp": _now - timedelta(days=2)},
]

_MOCK_ROUTES = [
    {"route_id": "route-001", "driver_id": None,
     "listing_ids": ["lst-001", "lst-003"],
     "waypoints": [
         {"label": "Start: Driver Base", "lat": 19.0760, "lng": 72.8777},
         {"label": "Pickup: 123 Main St", "lat": 19.0760, "lng": 72.8777},
         {"label": "Pickup: Supermart NM", "lat": 19.0330, "lng": 73.0297},
         {"label": "Drop: Community Kitchen", "lat": 19.0610, "lng": 72.9570},
     ],
     "total_km": 28.4, "est_minutes": 55, "status": "planned",
     "created_at": _now - timedelta(hours=1)},
]

_MOCK_FEEDBACK = [
    {"feedback_id": "fb-001", "user_id": _uid("donor@foodbridge.com"), "user_name": "Diana Donor", "role": "donor", "rating": 5, "message": "Love this platform! So easy to donate food.", "timestamp": _now - timedelta(days=2)},
    {"feedback_id": "fb-002", "user_id": _uid("receiver@foodbridge.com"), "user_name": "Rachel NGO", "role": "receiver", "rating": 4, "message": "The priority pickup works great, but I wish I could filter by exact distance.", "timestamp": _now - timedelta(hours=5)},
]

_MOCK_NOTIFICATIONS = [
    {"notif_id": "nt-001", "receiver_id": "all", "title": "Welcome to FoodBridge!", "message": "Check out the new Smart Container feature.", "type": "system", "created_at": _now - timedelta(days=1), "read": False},
]

# ════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ════════════════════════════════════════════════════════════

def create_platform_notification(title: str, message: str, n_type: str, receiver_id: str = "all") -> str:
    notif_id = str(uuid.uuid4())
    doc = {
        "notif_id":    notif_id,
        "receiver_id": receiver_id, # 'all' means all receivers see it
        "title":       title,
        "message":     message,
        "type":        n_type,
        "created_at":  datetime.now(timezone.utc),
        "read":        False
    }
    if db:
        db.collection("notifications").document(notif_id).set(doc)
    else:
        _MOCK_NOTIFICATIONS.append(doc)
    return notif_id

def get_user_notifications(receiver_id: str, limit: int = 20) -> List[dict]:
    if db:
        # Fetch notifications for this receiver or "all"
        docs_all = db.collection("notifications").where("receiver_id", "in", [receiver_id, "all"]).order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
        res = [d.to_dict() for d in docs_all]
        res.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return res
    
    # Mock fallback
    notifs = [n for n in _MOCK_NOTIFICATIONS if n.get("receiver_id") in (receiver_id, "all")]
    return sorted(notifs, key=lambda x: x.get("created_at") or "", reverse=True)

# ════════════════════════════════════════════════════════════
# FEEDBACK
# ════════════════════════════════════════════════════════════

def submit_feedback(user_id: str, user_name: str, role: str, rating: int, message: str) -> str:
    fb_id = str(uuid.uuid4())
    doc = {
        "feedback_id": fb_id,
        "user_id":     user_id,
        "user_name":   user_name,
        "role":        role,
        "rating":      rating,
        "message":     message,
        "timestamp":   datetime.now(timezone.utc),
    }
    if db:
        db.collection("feedback").document(fb_id).set(doc)
    else:
        _MOCK_FEEDBACK.append(doc)
    return fb_id

def get_all_feedback(limit: int = 50) -> List[dict]:
    if db:
        docs = db.collection("feedback").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
        return [d.to_dict() for d in docs]
    return sorted(_MOCK_FEEDBACK, key=lambda x: x.get("timestamp") or "", reverse=True)

