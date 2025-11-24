#!/usr/bin/env python3
"""
Generate VAPID keys for Web Push notifications
"""

try:
    import pywebpush
    
    vapid = pywebpush.generate_vapid_keys()
    
    print("\n=== VAPID Keys Generated ===\n")
    print("Add these to your backend .env file:\n")
    print(f"VAPID_PRIVATE_KEY={vapid['private_key']}")
    print(f"VAPID_PUBLIC_KEY={vapid['public_key']}")
    print(f"\nAdd the public key to your frontend .env file:\n")
    print(f"VITE_VAPID_PUBLIC_KEY={vapid['public_key']}")
    print("\n============================\n")
    
except ImportError:
    print("Error: pywebpush is not installed.")
    print("Install it with: pip install pywebpush")
    print("Or install all requirements: pip install -r requirements.txt")
