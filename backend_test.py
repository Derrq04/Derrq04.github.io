import requests
import unittest
import uuid
import json
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://efdf04cb-7389-44da-b389-e3a22e9d0ad5.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class ReverseMarketplaceAPITest(unittest.TestCase):
    def setUp(self):
        # Generate unique identifiers for test users
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.customer_email = f"customer_{timestamp}@test.com"
        self.seller_email = f"seller_{timestamp}@test.com"
        self.password = "Test123!"
        
        # Tokens for authenticated requests
        self.customer_token = None
        self.seller_token = None
        self.customer_id = None
        self.seller_id = None
        
        # Test data
        self.request_id = None
        self.offer_id = None

    def test_01_register_customer(self):
        """Test customer registration"""
        print("\n🔍 Testing customer registration...")
        
        payload = {
            "email": self.customer_email,
            "password": self.password,
            "full_name": "Test Customer",
            "user_type": "customer",
            "phone": "1234567890",
            "location": "Test Location"
        }
        
        response = requests.post(f"{API_URL}/register", json=payload)
        
        self.assertEqual(response.status_code, 200, f"Failed to register customer: {response.text}")
        data = response.json()
        self.assertIn("access_token", data, "No access token in response")
        self.assertIn("user", data, "No user data in response")
        self.assertEqual(data["user"]["email"], self.customer_email)
        self.assertEqual(data["user"]["user_type"], "customer")
        
        # Save token for later tests
        self.customer_token = data["access_token"]
        self.customer_id = data["user"]["id"]
        print("✅ Customer registration successful")

    def test_02_register_seller(self):
        """Test seller registration"""
        print("\n🔍 Testing seller registration...")
        
        payload = {
            "email": self.seller_email,
            "password": self.password,
            "full_name": "Test Seller",
            "user_type": "seller",
            "phone": "0987654321",
            "location": "Test Location",
            "business_name": "Test Business",
            "business_description": "This is a test business"
        }
        
        response = requests.post(f"{API_URL}/register", json=payload)
        
        self.assertEqual(response.status_code, 200, f"Failed to register seller: {response.text}")
        data = response.json()
        self.assertIn("access_token", data, "No access token in response")
        self.assertIn("user", data, "No user data in response")
        self.assertEqual(data["user"]["email"], self.seller_email)
        self.assertEqual(data["user"]["user_type"], "seller")
        self.assertEqual(data["user"]["business_name"], "Test Business")
        
        # Save token for later tests
        self.seller_token = data["access_token"]
        self.seller_id = data["user"]["id"]
        print("✅ Seller registration successful")

    def test_03_login(self):
        """Test login functionality"""
        print("\n🔍 Testing login...")
        
        # Test customer login
        payload = {
            "email": self.customer_email,
            "password": self.password
        }
        
        response = requests.post(f"{API_URL}/login", json=payload)
        
        self.assertEqual(response.status_code, 200, f"Failed to login as customer: {response.text}")
        data = response.json()
        self.assertIn("access_token", data, "No access token in response")
        self.assertEqual(data["user"]["email"], self.customer_email)
        
        # Test seller login
        payload = {
            "email": self.seller_email,
            "password": self.password
        }
        
        response = requests.post(f"{API_URL}/login", json=payload)
        
        self.assertEqual(response.status_code, 200, f"Failed to login as seller: {response.text}")
        data = response.json()
        self.assertIn("access_token", data, "No access token in response")
        self.assertEqual(data["user"]["email"], self.seller_email)
        
        print("✅ Login tests successful")

    def test_04_get_profile(self):
        """Test profile retrieval"""
        print("\n🔍 Testing profile retrieval...")
        
        # Test customer profile
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{API_URL}/profile", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get customer profile: {response.text}")
        data = response.json()
        self.assertEqual(data["email"], self.customer_email)
        
        # Test seller profile
        headers = {"Authorization": f"Bearer {self.seller_token}"}
        response = requests.get(f"{API_URL}/profile", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get seller profile: {response.text}")
        data = response.json()
        self.assertEqual(data["email"], self.seller_email)
        
        print("✅ Profile retrieval successful")

    def test_05_get_categories(self):
        """Test categories endpoint"""
        print("\n🔍 Testing categories endpoint...")
        
        response = requests.get(f"{API_URL}/categories")
        
        self.assertEqual(response.status_code, 200, f"Failed to get categories: {response.text}")
        categories = response.json()
        self.assertIsInstance(categories, list, "Categories should be a list")
        self.assertGreater(len(categories), 0, "Categories list should not be empty")
        
        print("✅ Categories endpoint successful")

    def test_06_create_request(self):
        """Test request creation by customer"""
        print("\n🔍 Testing request creation...")
        
        if not self.customer_token:
            self.skipTest("Customer token not available")
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        payload = {
            "title": "Test Request",
            "description": "This is a test request",
            "budget_min": 1000,
            "budget_max": 2000,
            "categories": ["Electronics & Gadgets", "Services"],
            "location": "Test Location",
            "timeline": "1 week",
            "quantity": 1
        }
        
        response = requests.post(f"{API_URL}/requests", json=payload, headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to create request: {response.text}")
        data = response.json()
        self.assertIn("id", data, "No request ID in response")
        self.assertEqual(data["title"], "Test Request")
        self.assertEqual(data["budget_min"], 1000)
        self.assertEqual(data["budget_max"], 2000)
        
        # Save request ID for later tests
        self.request_id = data["id"]
        print("✅ Request creation successful")

    def test_07_seller_cannot_create_request(self):
        """Test that sellers cannot create requests"""
        print("\n🔍 Testing seller cannot create request...")
        
        if not self.seller_token:
            self.skipTest("Seller token not available")
        
        headers = {"Authorization": f"Bearer {self.seller_token}"}
        payload = {
            "title": "Test Request",
            "description": "This is a test request",
            "budget_min": 1000,
            "budget_max": 2000,
            "categories": ["Electronics & Gadgets"],
            "location": "Test Location",
            "timeline": "1 week",
            "quantity": 1
        }
        
        response = requests.post(f"{API_URL}/requests", json=payload, headers=headers)
        
        self.assertEqual(response.status_code, 403, "Sellers should not be able to create requests")
        print("✅ Seller permission check successful")

    def test_08_get_requests(self):
        """Test retrieving all requests"""
        print("\n🔍 Testing get all requests...")
        
        if not self.customer_token:
            self.skipTest("Customer token not available")
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{API_URL}/requests", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get requests: {response.text}")
        requests_data = response.json()
        self.assertIsInstance(requests_data, list, "Requests should be a list")
        
        print("✅ Get all requests successful")

    def test_09_get_my_requests(self):
        """Test retrieving customer's own requests"""
        print("\n🔍 Testing get my requests...")
        
        if not self.customer_token or not self.request_id:
            self.skipTest("Customer token or request ID not available")
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{API_URL}/requests/my", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get my requests: {response.text}")
        requests_data = response.json()
        self.assertIsInstance(requests_data, list, "My requests should be a list")
        
        # Check if our created request is in the list
        request_ids = [req["id"] for req in requests_data]
        self.assertIn(self.request_id, request_ids, "Created request not found in my requests")
        
        print("✅ Get my requests successful")

    def test_10_get_request_by_id(self):
        """Test retrieving a specific request by ID"""
        print("\n🔍 Testing get request by ID...")
        
        if not self.customer_token or not self.request_id:
            self.skipTest("Customer token or request ID not available")
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{API_URL}/requests/{self.request_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get request by ID: {response.text}")
        request_data = response.json()
        self.assertEqual(request_data["id"], self.request_id)
        
        print("✅ Get request by ID successful")

    def test_11_create_offer(self):
        """Test offer creation by seller"""
        print("\n🔍 Testing offer creation...")
        
        if not self.seller_token or not self.request_id:
            self.skipTest("Seller token or request ID not available")
        
        headers = {"Authorization": f"Bearer {self.seller_token}"}
        payload = {
            "request_id": self.request_id,
            "price": 1500,
            "description": "This is a test offer",
            "delivery_details": "Delivery within 3 days",
            "terms": "Payment on delivery"
        }
        
        response = requests.post(f"{API_URL}/offers", json=payload, headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to create offer: {response.text}")
        data = response.json()
        self.assertIn("id", data, "No offer ID in response")
        self.assertEqual(data["request_id"], self.request_id)
        self.assertEqual(data["price"], 1500)
        
        # Save offer ID for later tests
        self.offer_id = data["id"]
        print("✅ Offer creation successful")

    def test_12_customer_cannot_create_offer(self):
        """Test that customers cannot create offers"""
        print("\n🔍 Testing customer cannot create offer...")
        
        if not self.customer_token or not self.request_id:
            self.skipTest("Customer token or request ID not available")
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        payload = {
            "request_id": self.request_id,
            "price": 1500,
            "description": "This is a test offer",
            "delivery_details": "Delivery within 3 days",
            "terms": "Payment on delivery"
        }
        
        response = requests.post(f"{API_URL}/offers", json=payload, headers=headers)
        
        self.assertEqual(response.status_code, 403, "Customers should not be able to create offers")
        print("✅ Customer permission check successful")

    def test_13_get_offers_for_request(self):
        """Test retrieving offers for a specific request"""
        print("\n🔍 Testing get offers for request...")
        
        if not self.customer_token or not self.request_id:
            self.skipTest("Customer token or request ID not available")
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.get(f"{API_URL}/offers/request/{self.request_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get offers for request: {response.text}")
        offers_data = response.json()
        self.assertIsInstance(offers_data, list, "Offers should be a list")
        
        # Check if our created offer is in the list
        if self.offer_id:
            offer_ids = [offer["id"] for offer in offers_data]
            self.assertIn(self.offer_id, offer_ids, "Created offer not found in offers for request")
        
        print("✅ Get offers for request successful")

    def test_14_get_my_offers(self):
        """Test retrieving seller's own offers"""
        print("\n🔍 Testing get my offers...")
        
        if not self.seller_token or not self.offer_id:
            self.skipTest("Seller token or offer ID not available")
        
        headers = {"Authorization": f"Bearer {self.seller_token}"}
        response = requests.get(f"{API_URL}/offers/my", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to get my offers: {response.text}")
        offers_data = response.json()
        self.assertIsInstance(offers_data, list, "My offers should be a list")
        
        # Check if our created offer is in the list
        offer_ids = [offer["id"] for offer in offers_data]
        self.assertIn(self.offer_id, offer_ids, "Created offer not found in my offers")
        
        print("✅ Get my offers successful")

    def test_15_accept_offer(self):
        """Test accepting an offer"""
        print("\n🔍 Testing accept offer...")
        
        if not self.customer_token or not self.offer_id:
            self.skipTest("Customer token or offer ID not available")
        
        headers = {"Authorization": f"Bearer {self.customer_token}"}
        response = requests.put(f"{API_URL}/offers/{self.offer_id}/accept", headers=headers)
        
        self.assertEqual(response.status_code, 200, f"Failed to accept offer: {response.text}")
        data = response.json()
        self.assertIn("message", data, "No message in response")
        
        # Verify offer status changed
        response = requests.get(f"{API_URL}/offers/request/{self.request_id}", headers=headers)
        offers_data = response.json()
        for offer in offers_data:
            if offer["id"] == self.offer_id:
                self.assertEqual(offer["status"], "accepted", "Offer status not updated to accepted")
        
        # Verify request status changed
        response = requests.get(f"{API_URL}/requests/{self.request_id}", headers=headers)
        request_data = response.json()
        self.assertEqual(request_data["status"], "offer_accepted", "Request status not updated to offer_accepted")
        
        print("✅ Accept offer successful")

    def test_16_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n🔍 Testing dashboard stats...")
        
        # Test customer stats
        if self.customer_token:
            headers = {"Authorization": f"Bearer {self.customer_token}"}
            response = requests.get(f"{API_URL}/dashboard/stats", headers=headers)
            
            self.assertEqual(response.status_code, 200, f"Failed to get customer stats: {response.text}")
            stats = response.json()
            self.assertIn("total_requests", stats, "No total_requests in customer stats")
            self.assertIn("active_requests", stats, "No active_requests in customer stats")
            self.assertIn("total_offers_received", stats, "No total_offers_received in customer stats")
        
        # Test seller stats
        if self.seller_token:
            headers = {"Authorization": f"Bearer {self.seller_token}"}
            response = requests.get(f"{API_URL}/dashboard/stats", headers=headers)
            
            self.assertEqual(response.status_code, 200, f"Failed to get seller stats: {response.text}")
            stats = response.json()
            self.assertIn("total_offers", stats, "No total_offers in seller stats")
            self.assertIn("accepted_offers", stats, "No accepted_offers in seller stats")
            self.assertIn("pending_offers", stats, "No pending_offers in seller stats")
        
        print("✅ Dashboard stats successful")

if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add tests in order
    test_suite.addTest(ReverseMarketplaceAPITest('test_01_register_customer'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_02_register_seller'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_03_login'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_04_get_profile'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_05_get_categories'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_06_create_request'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_07_seller_cannot_create_request'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_08_get_requests'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_09_get_my_requests'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_10_get_request_by_id'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_11_create_offer'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_12_customer_cannot_create_offer'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_13_get_offers_for_request'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_14_get_my_offers'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_15_accept_offer'))
    test_suite.addTest(ReverseMarketplaceAPITest('test_16_dashboard_stats'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
