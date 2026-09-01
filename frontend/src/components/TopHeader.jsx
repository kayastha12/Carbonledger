import React from 'react';

export default function TopHeader({
  activeTab,
  currentUser,
  currentSub,
  setShowUpgradeModal,
  handleLogout,
  themeText,
  themeSubtext,
  themeBorder
}) {
  return (
    <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
      <div>
        <h2 style={{ fontSize: '24px', fontWeight: '800', margin: 0, letterSpacing: '-0.5px' }}>{activeTab}</h2>
        <span style={{ fontSize: '12px', color: themeSubtext, marginTop: '2px', display: 'inline-block' }}>
          {activeTab === 'Dashboard' && 'Enterprise tenant GHG carbon accounting and CBAM compliance metrics'}
          {activeTab === 'Upload & Review' && 'Universal document intake with human-in-the-loop audit verification (⚡ 15 Tokens)'}
          {activeTab === 'Reports' && 'Download compliance CBAM declaration and GHG corporate inventory reports (⚡ 25 Tokens)'}
          {activeTab === 'AI Intelligence' && 'AI Sustainability Copilot, what-if simulations, and CBAM forecasting'}
          {activeTab === 'Subscription & Billing' && 'Manage enterprise subscription tiers, refill token quota, and view invoices'}
          {activeTab === 'Settings' && 'Workspace organization profile, emission factors region, and security'}
          {activeTab === 'Admin Console' && 'Platform governance, user management, manual token allocations, and audit trails'}
        </span>
      </div>

      {/* Right Header Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Token Badge */}
        <div 
          onClick={() => setShowUpgradeModal(true)}
          style={{
            padding: '6px 14px', borderRadius: '20px', cursor: 'pointer',
            backgroundColor: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)',
            color: '#10b981', fontSize: '12px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '6px',
            transition: 'all 0.2s'
          }}
          title="Click to upgrade plan or refill token quota">
          <span>⚡</span> {(currentUser?.token_balance || 0).toLocaleString()} Tokens
        </div>

        {/* Plan Tier Pill */}
        <span style={{
          fontSize: '11px', padding: '5px 12px', borderRadius: '20px', fontWeight: '800', textTransform: 'uppercase',
          backgroundColor: currentSub?.plan_tier === 'enterprise' ? 'rgba(139,92,246,0.15)' : (currentSub?.plan_tier === 'professional' ? 'rgba(59,130,246,0.15)' : 'rgba(16,185,129,0.15)'),
          color: currentSub?.plan_tier === 'enterprise' ? '#c084fc' : (currentSub?.plan_tier === 'professional' ? '#60a5fa' : '#34d399')
        }}>
          {currentSub?.plan_tier || 'Trial'} Tier
        </span>

        <div style={{ width: '1px', height: '20px', backgroundColor: themeBorder }}></div>

        {/* User Profile Pill & Sign Out */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: themeText }}>{currentUser?.full_name || 'User'}</div>
            <div style={{ fontSize: '10px', color: themeSubtext }}>{currentUser?.organization || 'Organization'}</div>
          </div>
          <button 
            onClick={handleLogout}
            style={{ padding: '6px 12px', borderRadius: '8px', background: 'rgba(239,68,68,0.12)', border: '1px solid #ef4444', color: '#f87171', cursor: 'pointer', fontSize: '11px', fontWeight: '700' }}>
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
}

