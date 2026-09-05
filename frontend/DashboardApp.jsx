import React, { useState, useEffect } from 'react';
import { API_BASE } from './src/config';
import AuthScreen from './src/components/AuthScreen';
import TopHeader from './src/components/TopHeader';
import Sidebar from './src/components/Sidebar';
import UpgradeModal from './src/components/UpgradeModal';
import LowTokenModal from './src/components/LowTokenModal';
import AdminModals from './src/components/AdminModals';

import DashboardTab from './src/components/DashboardTab';
import UploadReviewTab from './src/components/UploadReviewTab';
import ReportsTab from './src/components/ReportsTab';
import AIIntelligenceTab from './src/components/AIIntelligenceTab';
import SubscriptionTab from './src/components/SubscriptionTab';
import SettingsTab from './src/components/SettingsTab';
import AdminConsoleTab from './src/components/AdminConsoleTab';

export default function DashboardApp() {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [notificationToast, setNotificationToast] = useState('');

  // Authentication & SaaS User State
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('carbonledger_user');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });

  const [currentSub, setCurrentSub] = useState(() => {
    try {
      const saved = localStorage.getItem('carbonledger_sub');
      return saved ? JSON.parse(saved) : { plan_tier: 'trial', billing_cycle: 'monthly', status: 'trial', price_usd: 0, renewal_date: '2026-12-31', report_limit: 3 };
    } catch (e) {
      return { plan_tier: 'trial', billing_cycle: 'monthly', status: 'trial', price_usd: 0, renewal_date: '2026-12-31', report_limit: 3 };
    }
  });

  // Billing & Subscription States
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [billingHistory, setBillingHistory] = useState([]);
  const [tokenHistory, setTokenHistory] = useState([]);
  const [userActivities, setUserActivities] = useState([]);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showLowTokenModal, setShowLowTokenModal] = useState(false);
  const [lowTokenDetails, setLowTokenDetails] = useState({ required: 15, current: 0 });

  // Configurable Settings State
  const [carbonPrice, setCarbonPrice] = useState(85.0);

  // Universal Carbon Dataset Upload & Calculation States
  const [universalFile, setUniversalFile] = useState(null);
  const [universalStatus, setUniversalStatus] = useState('idle');
  const [universalResult, setUniversalResult] = useState(null);
  const [universalUploadId, setUniversalUploadId] = useState('');
  const [reviewedRecords, setReviewedRecords] = useState([]);
  const [parserResponse, setParserResponse] = useState(null);

  // AI Chat Assistant State
  const [chatMessages, setChatMessages] = useState([
    { sender: 'assistant', text: 'Hello! I am your AI Sustainability Assistant. I can analyze emissions, supplier footprints, or CBAM liability. How can I assist you today?' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Scenario Analysis State
  const [selectedStrategy, setSelectedStrategy] = useState('eaf_steel');
  const [scenarioResult, setScenarioResult] = useState(null);
  const [isScenarioLoading, setIsScenarioLoading] = useState(false);

  // Admin SaaS Console States
  const [adminSubTab, setAdminSubTab] = useState('overview');
  const [adminStats, setAdminStats] = useState(null);
  const [adminUsersList, setAdminUsersList] = useState([]);
  const [adminUserSearch, setAdminUserSearch] = useState('');
  const [adminRules, setAdminRules] = useState([]);
  const [adminFactors, setAdminFactors] = useState([]);
  const [adminAuditLogs, setAdminAuditLogs] = useState([]);
  
  // Admin Action Modals
  const [selectedAdminUser, setSelectedAdminUser] = useState(null);
  const [showAdjustTokensModal, setShowAdjustTokensModal] = useState(false);
  const [tokenAdjustType, setTokenAdjustType] = useState('add');
  const [tokenAdjustAmount, setTokenAdjustAmount] = useState(500);
  const [tokenAdjustReason, setTokenAdjustReason] = useState('Customer Support Bonus');
  
  const [showOverrideSubModal, setShowOverrideSubModal] = useState(false);
  const [subOverridePlan, setSubOverridePlan] = useState('starter');
  const [subOverrideCycle, setSubOverrideCycle] = useState('monthly');
  const [subOverrideStatus, setSubOverrideStatus] = useState('active');

  // Theme Styling Tokens
  const themeBg = isDarkMode ? '#080c14' : '#f8fafc';
  const themeCard = isDarkMode ? '#111827' : '#ffffff';
  const themeBorder = isDarkMode ? '#1f2937' : '#e2e8f0';
  const themeText = isDarkMode ? '#f3f4f6' : '#0f172a';
  const themeSubtext = isDarkMode ? '#9ca3af' : '#64748b';

  const showToast = (msg) => {
    setNotificationToast(msg);
    setTimeout(() => setNotificationToast(''), 4000);
  };

  const getAuthHeaders = () => {
    const token = localStorage.getItem('carbonledger_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    };
  };

  const refreshUserData = () => {
    const token = localStorage.getItem('carbonledger_token');
    if (!token) return;
    fetch(`${API_BASE}/api/v1/auth/me`, { headers: getAuthHeaders() })
      .then(res => res.json())
      .then(data => {
        if (data.user) {
          setCurrentUser(data.user);
          localStorage.setItem('carbonledger_user', JSON.stringify(data.user));
        }
        if (data.subscription) {
          setCurrentSub(data.subscription);
          localStorage.setItem('carbonledger_sub', JSON.stringify(data.subscription));
        }
      })
      .catch(() => {});
  };

  // Fetch Latest Upload Session for Dashboard & Reports Tab
  const fetchUserUploadData = () => {
    const token = localStorage.getItem('carbonledger_token');
    if (!token) return;
    fetch(`${API_BASE}/api/upload/latest`, { headers: getAuthHeaders() })
      .then(res => res.json())
      .then(data => {
        if (data && data.records && data.records.length > 0) {
          setUniversalResult(data);
        } else {
          setUniversalResult(null);
        }
      })
      .catch(() => {
        setUniversalResult(null);
      });
  };

  // Fetch Billing and Activity History
  const fetchBillingAndActivity = () => {
    fetch(`${API_BASE}/api/v1/user/billing/history`, { headers: getAuthHeaders() })
      .then(res => res.json()).then(data => setBillingHistory(data || [])).catch(() => {});
    fetch(`${API_BASE}/api/v1/user/tokens/history`, { headers: getAuthHeaders() })
      .then(res => res.json()).then(data => setTokenHistory(data || [])).catch(() => {});
    fetch(`${API_BASE}/api/v1/user/activity`, { headers: getAuthHeaders() })
      .then(res => res.json()).then(data => setUserActivities(data || [])).catch(() => {});
  };

  // Fetch Admin Console Data
  const fetchAdminData = () => {
    if (currentUser?.role !== 'admin') return;
    fetch(`${API_BASE}/api/v1/admin/dashboard-stats`, { headers: getAuthHeaders() })
      .then(res => res.json()).then(data => setAdminStats(data || null)).catch(() => {});
    fetch(`${API_BASE}/api/v1/admin/users`, { headers: getAuthHeaders() })
      .then(res => res.json()).then(data => setAdminUsersList(data || [])).catch(() => {});
    fetch(`${API_BASE}/api/v1/admin/rules`, { headers: getAuthHeaders() })
      .then(res => res.json()).then(data => setAdminRules(data || [])).catch(() => {});
    fetch(`${API_BASE}/api/v1/admin/factors`, { headers: getAuthHeaders() })
      .then(res => res.json()).then(data => setAdminFactors(data || [])).catch(() => {});
    fetch(`${API_BASE}/api/v1/admin/audit-logs`, { headers: getAuthHeaders() })
      .then(res => res.json()).then(data => setAdminAuditLogs(data || [])).catch(() => {});
  };

  useEffect(() => {
    if (currentUser) {
      refreshUserData();
      fetchUserUploadData();
      fetchBillingAndActivity();
      if (currentUser.role === 'admin') fetchAdminData();
    }
  }, [currentUser?.id, activeTab]);

  const handleLoginSuccess = (user, sub) => {
    setCurrentUser(user);
    if (sub) setCurrentSub(sub);
    showToast(`Welcome back, ${user.full_name}!`);
  };

  const handleLogout = () => {
    localStorage.removeItem('carbonledger_token');
    localStorage.removeItem('carbonledger_user');
    localStorage.removeItem('carbonledger_sub');
    setCurrentUser(null);
    setCurrentSub({ plan_tier: 'trial', billing_cycle: 'monthly', status: 'trial', price_usd: 0, renewal_date: '2026-12-31', report_limit: 3 });
    setUniversalResult(null);
    setActiveTab('Dashboard');
    showToast('Signed out successfully.');
  };

  const handleUpgradePlan = (planKey, cycle) => {
    fetch(`${API_BASE}/api/v1/user/subscription/upgrade`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ plan_tier: planKey, billing_cycle: cycle, payment_method: 'Visa ending in 4242' })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (status !== 200) throw new Error(body.detail || 'Upgrade failed.');
      setShowUpgradeModal(false);
      showToast(body.message);
      refreshUserData();
      fetchBillingAndActivity();
    })
    .catch(err => alert(err.message));
  };

  const handleAdminAdjustTokens = () => {
    if (!selectedAdminUser) return;
    fetch(`${API_BASE}/api/v1/admin/users/${selectedAdminUser.id}/tokens`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        adjustment_type: tokenAdjustType,
        amount: parseInt(tokenAdjustAmount) || 0,
        reason: tokenAdjustReason
      })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (status !== 200) throw new Error(body.detail || 'Failed to adjust tokens');
      setShowAdjustTokensModal(false);
      showToast(body.message);
      fetchAdminData();
    })
    .catch(err => alert(err.message));
  };

  const handleAdminOverrideSub = () => {
    if (!selectedAdminUser) return;
    fetch(`${API_BASE}/api/v1/admin/users/${selectedAdminUser.id}/subscription`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        plan_tier: subOverridePlan,
        billing_cycle: subOverrideCycle,
        status: subOverrideStatus,
        days_to_extend: 30
      })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (status !== 200) throw new Error(body.detail || 'Failed to override plan');
      setShowOverrideSubModal(false);
      showToast(body.message);
      fetchAdminData();
    })
    .catch(err => alert(err.message));
  };

  const handleAdminToggleUser = (userId) => {
    fetch(`${API_BASE}/api/v1/admin/users/${userId}/status`, {
      method: 'PATCH',
      headers: getAuthHeaders()
    }).then(() => {
      showToast('User status updated.');
      fetchAdminData();
    });
  };

  const handleAdminDeleteUser = (userId) => {
    if (!window.confirm('Are you sure you want to delete this user and all associated tenant records?')) return;
    fetch(`${API_BASE}/api/v1/admin/users/${userId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (status !== 200) throw new Error(body.detail || 'Failed to delete user');
      showToast(body.message);
      fetchAdminData();
    })
    .catch(err => alert(err.message));
  };

  // Pricing Plans Matrix
  const plans = [
    {
      key: 'trial',
      name: 'Free Trial',
      monthly_price: 0,
      yearly_price: 0,
      tokens: 100,
      reports: '3 Report Exports',
      features: ['Basic Scope 1/2/3 Extraction', 'Standard OCR Quality', '7-Day Validity', 'Community Support'],
      popular: false,
      cta: 'Current Plan'
    },
    {
      key: 'starter',
      name: 'Starter Plan',
      monthly_price: 49,
      yearly_price: 470,
      tokens: 1000,
      reports: '25 Report Exports / mo',
      features: ['1,000 AI Tokens / month', 'High-Speed OCR Pipeline', 'Multi-file ZIP Intake', 'Email Support (24h)'],
      popular: false,
      cta: 'Upgrade to Starter'
    },
    {
      key: 'professional',
      name: 'Professional Plan',
      monthly_price: 149,
      yearly_price: 1430,
      tokens: 5000,
      reports: 'Unlimited Reports',
      features: ['5,000 AI Tokens / month', 'Custom Emission Factor Overrides', 'Priority GPU RAG Assistant', 'CBAM Anomaly Safety Gate', 'Priority Support (4h)'],
      popular: true,
      cta: 'Upgrade to Pro'
    },
    {
      key: 'enterprise',
      name: 'Enterprise Plan',
      monthly_price: 499,
      yearly_price: 4790,
      tokens: 25000,
      reports: 'Unlimited Reports',
      features: ['25,000 AI Tokens / month', 'Unlimited Custom Emission Factors', 'Dedicated Inference Cluster', 'Custom API Integrations', '24/7 Dedicated Account Mgr'],
      popular: false,
      cta: 'Upgrade to Enterprise'
    }
  ];

  const getAllowedTabs = () => {
    const tabs = [
      { name: 'Dashboard', icon: '📊' },
      { name: 'Upload & Review', icon: '📤' },
      { name: 'Reports', icon: '📑' },
      { name: 'AI Intelligence', icon: '🧠' },
      { name: 'Subscription & Billing', icon: '💳' },
      { name: 'Settings', icon: '⚙️' }
    ];
    if (currentUser?.role === 'admin') {
      tabs.push({ name: 'Admin Console', icon: '🛡️' });
    }
    return tabs;
  };

  // If user is not authenticated, render AuthScreen
  if (!currentUser) {
    return (
      <AuthScreen
        onLoginSuccess={handleLoginSuccess}
        isDarkMode={isDarkMode}
        themeText={themeText}
        themeSubtext={themeSubtext}
        themeBorder={themeBorder}
        themeCard={themeCard}
      />
    );
  }

  return (
    <div style={{ backgroundColor: themeBg, color: themeText, minHeight: '100vh', display: 'flex', fontFamily: 'Outfit, Inter, sans-serif' }}>
      
      {/* Toast Notification */}
      {notificationToast && (
        <div style={{
          position: 'fixed', top: '24px', right: '24px', zIndex: 9999,
          padding: '14px 20px', borderRadius: '12px', backgroundColor: '#10b981',
          color: '#080c14', fontWeight: '800', fontSize: '13px', boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
          display: 'flex', alignItems: 'center', gap: '8px'
        }}>
          <span>🌿</span> {notificationToast}
        </div>
      )}

      {/* Upgrade Modal */}
      <UpgradeModal
        showUpgradeModal={showUpgradeModal}
        setShowUpgradeModal={setShowUpgradeModal}
        currentSub={currentSub}
        billingCycle={billingCycle}
        setBillingCycle={setBillingCycle}
        plans={plans}
        handleUpgradePlan={handleUpgradePlan}
        isDarkMode={isDarkMode}
        themeCard={themeCard}
        themeBorder={themeBorder}
        themeText={themeText}
        themeSubtext={themeSubtext}
      />

      {/* Low Token Alert Modal */}
      <LowTokenModal
        showLowTokenModal={showLowTokenModal}
        setShowLowTokenModal={setShowLowTokenModal}
        setShowUpgradeModal={setShowUpgradeModal}
        lowTokenDetails={lowTokenDetails}
        themeCard={themeCard}
        themeBorder={themeBorder}
        themeText={themeText}
        themeSubtext={themeSubtext}
      />

      {/* Admin Adjust Tokens & Override Sub Modals */}
      <AdminModals
        showAdjustTokensModal={showAdjustTokensModal}
        setShowAdjustTokensModal={setShowAdjustTokensModal}
        selectedAdminUser={selectedAdminUser}
        tokenAdjustType={tokenAdjustType}
        setTokenAdjustType={setTokenAdjustType}
        tokenAdjustAmount={tokenAdjustAmount}
        setTokenAdjustAmount={setTokenAdjustAmount}
        tokenAdjustReason={tokenAdjustReason}
        setTokenAdjustReason={setTokenAdjustReason}
        handleAdminAdjustTokens={handleAdminAdjustTokens}
        showOverrideSubModal={showOverrideSubModal}
        setShowOverrideSubModal={setShowOverrideSubModal}
        subOverridePlan={subOverridePlan}
        setSubOverridePlan={setSubOverridePlan}
        subOverrideCycle={subOverrideCycle}
        setSubOverrideCycle={setSubOverrideCycle}
        subOverrideStatus={subOverrideStatus}
        setSubOverrideStatus={setSubOverrideStatus}
        handleAdminOverrideSub={handleAdminOverrideSub}
        isDarkMode={isDarkMode}
        themeCard={themeCard}
        themeBorder={themeBorder}
        themeText={themeText}
        themeSubtext={themeSubtext}
      />

      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        currentSub={currentSub}
        setShowUpgradeModal={setShowUpgradeModal}
        isDarkMode={isDarkMode}
        setIsDarkMode={setIsDarkMode}
        getAllowedTabs={getAllowedTabs}
        themeCard={themeCard}
        themeBorder={themeBorder}
        themeText={themeText}
        themeSubtext={themeSubtext}
      />

      {/* Main Workspace Area */}
      <main style={{ flex: 1, padding: '32px 40px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <TopHeader
          activeTab={activeTab}
          currentUser={currentUser}
          currentSub={currentSub}
          setShowUpgradeModal={setShowUpgradeModal}
          handleLogout={handleLogout}
          themeText={themeText}
          themeSubtext={themeSubtext}
          themeBorder={themeBorder}
        />

        {activeTab === 'Dashboard' && (
          <DashboardTab
            currentUser={currentUser}
            currentSub={currentSub}
            universalResult={universalResult}
            userActivities={userActivities}
            carbonPrice={carbonPrice}
            setActiveTab={setActiveTab}
            isDarkMode={isDarkMode}
            themeCard={themeCard}
            themeBorder={themeBorder}
            themeText={themeText}
            themeSubtext={themeSubtext}
          />
        )}

        {activeTab === 'Upload & Review' && (
          <UploadReviewTab
            currentUser={currentUser}
            universalFile={universalFile}
            setUniversalFile={setUniversalFile}
            universalStatus={universalStatus}
            setUniversalStatus={setUniversalStatus}
            universalUploadId={universalUploadId}
            setUniversalUploadId={setUniversalUploadId}
            reviewedRecords={reviewedRecords}
            setReviewedRecords={setReviewedRecords}
            setParserResponse={setParserResponse}
            showToast={showToast}
            refreshUserData={refreshUserData}
            fetchUserUploadData={fetchUserUploadData}
            fetchBillingAndActivity={fetchBillingAndActivity}
            setActiveTab={setActiveTab}
            setLowTokenDetails={setLowTokenDetails}
            setShowLowTokenModal={setShowLowTokenModal}
            getAuthHeaders={getAuthHeaders}
            isDarkMode={isDarkMode}
            themeCard={themeCard}
            themeBorder={themeBorder}
            themeText={themeText}
            themeSubtext={themeSubtext}
          />
        )}

        {activeTab === 'Reports' && (
          <ReportsTab
            universalResult={universalResult}
            currentUser={currentUser}
            currentSub={currentSub}
            getAuthHeaders={getAuthHeaders}
            showToast={showToast}
            isDarkMode={isDarkMode}
            themeCard={themeCard}
            themeBorder={themeBorder}
            themeText={themeText}
            themeSubtext={themeSubtext}
          />
        )}

        {activeTab === 'AI Intelligence' && (
          <AIIntelligenceTab
            currentUser={currentUser}
            chatMessages={chatMessages}
            setChatMessages={setChatMessages}
            chatInput={chatInput}
            setChatInput={setChatInput}
            isChatLoading={isChatLoading}
            setIsChatLoading={setIsChatLoading}
            selectedStrategy={selectedStrategy}
            setSelectedStrategy={setSelectedStrategy}
            scenarioResult={scenarioResult}
            setScenarioResult={setScenarioResult}
            isScenarioLoading={isScenarioLoading}
            setIsScenarioLoading={setIsScenarioLoading}
            setLowTokenDetails={setLowTokenDetails}
            setShowLowTokenModal={setShowLowTokenModal}
            refreshUserData={refreshUserData}
            getAuthHeaders={getAuthHeaders}
            isDarkMode={isDarkMode}
            themeCard={themeCard}
            themeBorder={themeBorder}
            themeText={themeText}
            themeSubtext={themeSubtext}
          />
        )}

        {activeTab === 'Subscription & Billing' && (
          <SubscriptionTab
            currentUser={currentUser}
            currentSub={currentSub}
            billingHistory={billingHistory}
            tokenHistory={tokenHistory}
            setShowUpgradeModal={setShowUpgradeModal}
            isDarkMode={isDarkMode}
            themeCard={themeCard}
            themeBorder={themeBorder}
            themeText={themeText}
            themeSubtext={themeSubtext}
          />
        )}

        {activeTab === 'Settings' && (
          <SettingsTab
            currentUser={currentUser}
            setCurrentUser={setCurrentUser}
            getAuthHeaders={getAuthHeaders}
            showToast={showToast}
            isDarkMode={isDarkMode}
            themeCard={themeCard}
            themeBorder={themeBorder}
            themeText={themeText}
            themeSubtext={themeSubtext}
          />
        )}

        {activeTab === 'Admin Console' && currentUser?.role === 'admin' && (
          <AdminConsoleTab
            adminSubTab={adminSubTab}
            setAdminSubTab={setAdminSubTab}
            adminStats={adminStats}
            adminUsersList={adminUsersList}
            adminUserSearch={adminUserSearch}
            setAdminUserSearch={setAdminUserSearch}
            adminRules={adminRules}
            adminFactors={adminFactors}
            adminAuditLogs={adminAuditLogs}
            currentUser={currentUser}
            setSelectedAdminUser={setSelectedAdminUser}
            setShowAdjustTokensModal={setShowAdjustTokensModal}
            setSubOverridePlan={setSubOverridePlan}
            setShowOverrideSubModal={setShowOverrideSubModal}
            handleAdminToggleUser={handleAdminToggleUser}
            handleAdminDeleteUser={handleAdminDeleteUser}
            fetchAdminData={fetchAdminData}
            showToast={showToast}
            getAuthHeaders={getAuthHeaders}
            isDarkMode={isDarkMode}
            themeCard={themeCard}
            themeBorder={themeBorder}
            themeText={themeText}
            themeSubtext={themeSubtext}
          />
        )}
      </main>

    </div>
  );
}

