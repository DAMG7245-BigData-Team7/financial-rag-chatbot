#!/usr/bin/env python3
"""
Test AURELIA Chatbot System
Quick test of backend and frontend integration
"""

import requests
import time
import json

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8000"

    print("🧪 TESTING AURELIA CHATBOT API")
    print("=" * 40)

    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            data = response.json()
            print(f"   API Version: {data.get('version')}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")

    # Test 2: Health check
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("system_ready"):
                print("✅ Health check passed - System ready")
                print(f"   Corpus: {data['corpus_info']['total_documents']} documents")
            else:
                print("⚠️  Health check shows system not ready")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")

    # Test 3: Stats
    print("\n3. Testing stats endpoint...")
    try:
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats endpoint working")
            print(f"   Total vectors: {data.get('total_vectors')}")
            print(f"   Available filters: {data.get('available_filters')}")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")

    # Test 4: Suggestions
    print("\n4. Testing suggestions endpoint...")
    try:
        response = requests.get(f"{base_url}/suggestions")
        if response.status_code == 200:
            suggestions = response.json()
            print(f"✅ Suggestions endpoint working ({len(suggestions)} suggestions)")
        else:
            print(f"❌ Suggestions endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Suggestions endpoint error: {e}")

    # Test 5: Question answering
    print("\n5. Testing question answering...")
    test_question = "What is the blsprice function used for?"

    try:
        payload = {"question": test_question}
        response = requests.post(f"{base_url}/ask", json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print("✅ Question answering working!")
            print(f"   Question: {data['question']}")
            print(f"   Processing time: {data['processing_time']:.2f}s")
            print(f"   Sources found: {len(data['sources'])}")
            print(f"   Answer preview: {data['answer'][:100]}...")
        else:
            print(f"❌ Question answering failed: {response.status_code}")
            print(f"   Error: {response.text}")

    except Exception as e:
        print(f"❌ Question answering error: {e}")

    # Test 6: Filtered search
    print("\n6. Testing filtered search...")
    try:
        payload = {
            "question": "portfolio optimization",
            "filter_type": "code"
        }
        response = requests.post(f"{base_url}/ask", json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print("✅ Filtered search working!")
            print(f"   Filter applied: {data.get('filter_applied')}")
            print(f"   Sources found: {len(data['sources'])}")
        else:
            print(f"❌ Filtered search failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Filtered search error: {e}")

    print("\n🎯 API TESTING COMPLETE")

def check_frontend():
    """Check if frontend is accessible"""
    print("\n🌐 CHECKING FRONTEND ACCESSIBILITY")
    print("=" * 40)

    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible at http://localhost:8501")
        else:
            print(f"⚠️  Frontend returned status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Frontend not accessible - may not be running")
    except Exception as e:
        print(f"❌ Frontend check error: {e}")

def main():
    """Main test function"""
    print("🧪 AURELIA CHATBOT SYSTEM TEST")
    print("=" * 50)

    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            test_api_endpoints()
        else:
            print("❌ Backend is not responding properly")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running")
        print("   Please start with: python start_chatbot.py")
        return
    except Exception as e:
        print(f"❌ Backend check error: {e}")
        return

    check_frontend()

    print("\n🎉 TESTING COMPLETE!")
    print("If all tests passed, your chatbot system is ready to use!")

if __name__ == "__main__":
    main()