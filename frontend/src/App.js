import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios interceptor for auth
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Components
const LoginRegister = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    user_type: 'customer',
    phone: '',
    location: '',
    business_name: '',
    business_description: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/login' : '/register';
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : formData;

      const response = await axios.post(`${API}${endpoint}`, payload);
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      onLogin(response.data.user);
    } catch (error) {
      alert(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">
          {isLogin ? 'Login' : 'Join Marketplace'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
          
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />

          {!isLogin && (
            <>
              <input
                type="text"
                name="full_name"
                placeholder="Full Name"
                value={formData.full_name}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />

              <select
                name="user_type"
                value={formData.user_type}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="customer">Customer (I want to buy)</option>
                <option value="seller">Seller (I want to sell)</option>
              </select>

              <input
                type="tel"
                name="phone"
                placeholder="Phone Number"
                value={formData.phone}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              <input
                type="text"
                name="location"
                placeholder="Location (e.g., Nairobi)"
                value={formData.location}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              {formData.user_type === 'seller' && (
                <>
                  <input
                    type="text"
                    name="business_name"
                    placeholder="Business Name"
                    value={formData.business_name}
                    onChange={handleChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <textarea
                    name="business_description"
                    placeholder="Business Description"
                    value={formData.business_description}
                    onChange={handleChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="3"
                  />
                </>
              )}
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700 transition duration-200 font-semibold"
          >
            {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-600 hover:text-blue-800 font-semibold"
          >
            {isLogin ? 'Register' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  );
};

const Dashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState(user.user_type === 'customer' ? 'my-requests' : 'browse-requests');
  const [requests, setRequests] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [offers, setOffers] = useState([]);
  const [myOffers, setMyOffers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [stats, setStats] = useState({});
  const [showCreateRequest, setShowCreateRequest] = useState(false);
  const [showCreateOffer, setShowCreateOffer] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    try {
      // Load categories
      const categoriesRes = await axios.get(`${API}/categories`);
      setCategories(categoriesRes.data);

      // Load stats
      const statsRes = await axios.get(`${API}/dashboard/stats`);
      setStats(statsRes.data);

      if (activeTab === 'browse-requests') {
        const requestsRes = await axios.get(`${API}/requests`);
        setRequests(requestsRes.data);
      } else if (activeTab === 'my-requests') {
        const myRequestsRes = await axios.get(`${API}/requests/my`);
        setMyRequests(myRequestsRes.data);
      } else if (activeTab === 'my-offers') {
        const myOffersRes = await axios.get(`${API}/offers/my`);
        setMyOffers(myOffersRes.data);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const CreateRequestForm = () => {
    const [formData, setFormData] = useState({
      title: '',
      description: '',
      budget_min: '',
      budget_max: '',
      categories: [],
      location: '',
      timeline: '',
      quantity: 1
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/requests`, {
          ...formData,
          budget_min: parseFloat(formData.budget_min),
          budget_max: parseFloat(formData.budget_max),
          quantity: parseInt(formData.quantity)
        });
        setShowCreateRequest(false);
        loadData();
        alert('Request created successfully!');
      } catch (error) {
        alert('Error creating request');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-bold mb-4">Create New Request</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              placeholder="Request Title"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              className="w-full p-3 border rounded-lg"
              required
            />
            
            <textarea
              placeholder="Detailed Description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full p-3 border rounded-lg"
              rows="4"
              required
            />

            <div className="grid grid-cols-2 gap-4">
              <input
                type="number"
                placeholder="Min Budget (KES)"
                value={formData.budget_min}
                onChange={(e) => setFormData({...formData, budget_min: e.target.value})}
                className="w-full p-3 border rounded-lg"
                required
              />
              <input
                type="number"
                placeholder="Max Budget (KES)"
                value={formData.budget_max}
                onChange={(e) => setFormData({...formData, budget_max: e.target.value})}
                className="w-full p-3 border rounded-lg"
                required
              />
            </div>

            <select
              multiple
              value={formData.categories}
              onChange={(e) => setFormData({...formData, categories: Array.from(e.target.selectedOptions, option => option.value)})}
              className="w-full p-3 border rounded-lg"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>

            <input
              type="text"
              placeholder="Location (optional)"
              value={formData.location}
              onChange={(e) => setFormData({...formData, location: e.target.value})}
              className="w-full p-3 border rounded-lg"
            />

            <input
              type="text"
              placeholder="Timeline (e.g., Within 1 week)"
              value={formData.timeline}
              onChange={(e) => setFormData({...formData, timeline: e.target.value})}
              className="w-full p-3 border rounded-lg"
            />

            <input
              type="number"
              placeholder="Quantity"
              value={formData.quantity}
              onChange={(e) => setFormData({...formData, quantity: e.target.value})}
              className="w-full p-3 border rounded-lg"
              min="1"
            />

            <div className="flex gap-4">
              <button
                type="submit"
                className="flex-1 bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700"
              >
                Create Request
              </button>
              <button
                type="button"
                onClick={() => setShowCreateRequest(false)}
                className="flex-1 bg-gray-500 text-white p-3 rounded-lg hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const CreateOfferForm = () => {
    const [formData, setFormData] = useState({
      price: '',
      description: '',
      delivery_details: '',
      terms: ''
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/offers`, {
          ...formData,
          request_id: selectedRequest.id,
          price: parseFloat(formData.price)
        });
        setShowCreateOffer(false);
        setSelectedRequest(null);
        alert('Offer submitted successfully!');
      } catch (error) {
        alert('Error creating offer');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-2xl">
          <h3 className="text-xl font-bold mb-4">Submit Offer</h3>
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold">{selectedRequest?.title}</h4>
            <p className="text-sm text-gray-600">Budget: KES {selectedRequest?.budget_min} - {selectedRequest?.budget_max}</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="number"
              placeholder="Your Price (KES)"
              value={formData.price}
              onChange={(e) => setFormData({...formData, price: e.target.value})}
              className="w-full p-3 border rounded-lg"
              required
            />
            
            <textarea
              placeholder="Offer Description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full p-3 border rounded-lg"
              rows="4"
              required
            />

            <textarea
              placeholder="Delivery Details"
              value={formData.delivery_details}
              onChange={(e) => setFormData({...formData, delivery_details: e.target.value})}
              className="w-full p-3 border rounded-lg"
              rows="3"
              required
            />

            <textarea
              placeholder="Terms & Conditions (optional)"
              value={formData.terms}
              onChange={(e) => setFormData({...formData, terms: e.target.value})}
              className="w-full p-3 border rounded-lg"
              rows="2"
            />

            <div className="flex gap-4">
              <button
                type="submit"
                className="flex-1 bg-green-600 text-white p-3 rounded-lg hover:bg-green-700"
              >
                Submit Offer
              </button>
              <button
                type="button"
                onClick={() => {setShowCreateOffer(false); setSelectedRequest(null);}}
                className="flex-1 bg-gray-500 text-white p-3 rounded-lg hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const RequestCard = ({ request, showOfferButton = false }) => (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{request.title}</h3>
        <span className={`px-3 py-1 rounded-full text-sm ${
          request.status === 'open' ? 'bg-green-100 text-green-800' : 
          request.status === 'offer_accepted' ? 'bg-blue-100 text-blue-800' : 
          'bg-gray-100 text-gray-800'
        }`}>
          {request.status.replace('_', ' ').toUpperCase()}
        </span>
      </div>
      
      <p className="text-gray-600 mb-4">{request.description}</p>
      
      <div className="grid grid-cols-2 gap-4 text-sm text-gray-500 mb-4">
        <div>
          <span className="font-semibold">Budget:</span> KES {request.budget_min} - {request.budget_max}
        </div>
        <div>
          <span className="font-semibold">Quantity:</span> {request.quantity}
        </div>
        {request.location && (
          <div>
            <span className="font-semibold">Location:</span> {request.location}
          </div>
        )}
        {request.timeline && (
          <div>
            <span className="font-semibold">Timeline:</span> {request.timeline}
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {request.categories.map(cat => (
          <span key={cat} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
            {cat}
          </span>
        ))}
      </div>

      <div className="flex gap-2">
        {showOfferButton && request.status === 'open' && (
          <button
            onClick={() => {setSelectedRequest(request); setShowCreateOffer(true);}}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Submit Offer
          </button>
        )}
        {user.user_type === 'customer' && (
          <button
            onClick={() => viewOffers(request.id)}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            View Offers
          </button>
        )}
      </div>
    </div>
  );

  const viewOffers = async (requestId) => {
    try {
      const response = await axios.get(`${API}/offers/request/${requestId}`);
      setOffers(response.data);
      setActiveTab('view-offers');
    } catch (error) {
      alert('Error loading offers');
    }
  };

  const acceptOffer = async (offerId) => {
    try {
      await axios.put(`${API}/offers/${offerId}/accept`);
      alert('Offer accepted! Payment process will begin.');
      loadData();
    } catch (error) {
      alert('Error accepting offer');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">Reverse Marketplace</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user.full_name}</span>
              <span className={`px-2 py-1 rounded text-xs ${
                user.subscription_status === 'trial' ? 'bg-yellow-100 text-yellow-800' : 
                'bg-green-100 text-green-800'
              }`}>
                {user.subscription_status.toUpperCase()}
              </span>
              <button
                onClick={onLogout}
                className="text-gray-500 hover:text-gray-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {user.user_type === 'customer' ? (
            <>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900">My Requests</h3>
                <p className="text-3xl font-bold text-blue-600">{stats.total_requests || 0}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900">Active Requests</h3>
                <p className="text-3xl font-bold text-green-600">{stats.active_requests || 0}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900">Offers Received</h3>
                <p className="text-3xl font-bold text-purple-600">{stats.total_offers_received || 0}</p>
              </div>
            </>
          ) : (
            <>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900">My Offers</h3>
                <p className="text-3xl font-bold text-blue-600">{stats.total_offers || 0}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900">Accepted</h3>
                <p className="text-3xl font-bold text-green-600">{stats.accepted_offers || 0}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900">Pending</h3>
                <p className="text-3xl font-bold text-yellow-600">{stats.pending_offers || 0}</p>
              </div>
            </>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {user.user_type === 'customer' && (
              <button
                onClick={() => setActiveTab('my-requests')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'my-requests'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                My Requests
              </button>
            )}
            
            <button
              onClick={() => setActiveTab('browse-requests')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'browse-requests'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {user.user_type === 'customer' ? 'Browse Requests' : 'Browse Requests'}
            </button>

            {user.user_type === 'seller' && (
              <button
                onClick={() => setActiveTab('my-offers')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'my-offers'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                My Offers
              </button>
            )}
          </nav>
        </div>

        {/* Action Buttons */}
        <div className="mb-6">
          {user.user_type === 'customer' && activeTab === 'my-requests' && (
            <button
              onClick={() => setShowCreateRequest(true)}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
            >
              + Create New Request
            </button>
          )}
        </div>

        {/* Content */}
        <div>
          {activeTab === 'my-requests' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">My Requests</h2>
              {myRequests.length === 0 ? (
                <p className="text-gray-500">No requests yet. Create your first request!</p>
              ) : (
                myRequests.map(request => (
                  <RequestCard key={request.id} request={request} />
                ))
              )}
            </div>
          )}

          {activeTab === 'browse-requests' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">
                {user.user_type === 'seller' ? 'Available Requests' : 'All Requests'}
              </h2>
              {requests.length === 0 ? (
                <p className="text-gray-500">No requests available.</p>
              ) : (
                requests.map(request => (
                  <RequestCard 
                    key={request.id} 
                    request={request} 
                    showOfferButton={user.user_type === 'seller'}
                  />
                ))
              )}
            </div>
          )}

          {activeTab === 'my-offers' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">My Offers</h2>
              {myOffers.length === 0 ? (
                <p className="text-gray-500">No offers yet. Browse requests and submit offers!</p>
              ) : (
                myOffers.map(offer => (
                  <div key={offer.id} className="bg-white rounded-lg shadow-md p-6 mb-4">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-lg font-semibold">{offer.request_title}</h3>
                      <span className={`px-3 py-1 rounded-full text-sm ${
                        offer.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        offer.status === 'accepted' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {offer.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-2">{offer.description}</p>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><span className="font-semibold">My Price:</span> KES {offer.price}</div>
                      <div><span className="font-semibold">Request Budget:</span> {offer.request_budget}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'view-offers' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Offers for Request</h2>
              <button 
                onClick={() => setActiveTab('my-requests')}
                className="mb-4 text-blue-600 hover:text-blue-800"
              >
                ← Back to My Requests
              </button>
              {offers.length === 0 ? (
                <p className="text-gray-500">No offers yet for this request.</p>
              ) : (
                offers.map(offer => (
                  <div key={offer.id} className="bg-white rounded-lg shadow-md p-6 mb-4">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-lg font-semibold">{offer.seller_name}</h3>
                      <span className={`px-3 py-1 rounded-full text-sm ${
                        offer.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        offer.status === 'accepted' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {offer.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-4">{offer.description}</p>
                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-500 mb-4">
                      <div><span className="font-semibold">Price:</span> KES {offer.price}</div>
                      <div><span className="font-semibold">Delivery:</span> {offer.delivery_details}</div>
                    </div>
                    {offer.status === 'pending' && (
                      <button
                        onClick={() => acceptOffer(offer.id)}
                        className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                      >
                        Accept Offer
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showCreateRequest && <CreateRequestForm />}
      {showCreateOffer && <CreateOfferForm />}
    </div>
  );
};

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="App">
      {user ? (
        <Dashboard user={user} onLogout={handleLogout} />
      ) : (
        <LoginRegister onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;
