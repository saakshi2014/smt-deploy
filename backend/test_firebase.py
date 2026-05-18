import sys
import os

# Add project root to path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_config import initialize_firebase, get_firestore_client


def test_connection():
    print("\n── TEST 1: Firebase Connection ──────────────────")
    try:
        initialize_firebase()
        print("✅ PASS — Firebase Admin SDK initialised")
        return True
    except Exception as e:
        print(f"❌ FAIL — {e}")
        return False


def test_write():
    print("\n── TEST 2: Firestore Write ───────────────────────")
    try:
        db = get_firestore_client()
        db.collection('_test').document('day2_test').set({
            'message': 'Day 2 test passed',
            'value': 42
        })
        print("✅ PASS — Document written to Firestore")
        return True
    except Exception as e:
        print(f"❌ FAIL — {e}")
        return False


def test_read():
    print("\n── TEST 3: Firestore Read ────────────────────────")
    try:
        db = get_firestore_client()
        doc = db.collection('_test').document('day2_test').get()
        if doc.exists:
            print(f"✅ PASS — Document read back: {doc.to_dict()}")
            return True
        else:
            print("❌ FAIL — Document not found after writing")
            return False
    except Exception as e:
        print(f"❌ FAIL — {e}")
        return False


def test_delete():
    print("\n── TEST 4: Firestore Delete ──────────────────────")
    try:
        db = get_firestore_client()
        db.collection('_test').document('day2_test').delete()
        print("✅ PASS — Test document deleted cleanly")
        return True
    except Exception as e:
        print(f"❌ FAIL — {e}")
        return False


def run_all_tests():
    print("=" * 52)
    print("   DAY 2 — Firebase Connection Test Suite")
    print("=" * 52)

    results = [
        test_connection(),
        test_write(),
        test_read(),
        test_delete()
    ]

    passed = sum(results)
    total  = len(results)

    print("\n── RESULTS ───────────────────────────────────────")
    if passed == total:
        print(f"✅ ALL {total} TESTS PASSED — Firebase is fully working!")
    else:
        print(f"⚠️  {passed}/{total} tests passed — check failures above")
    print("=" * 52)


if __name__ == '__main__':
    run_all_tests()