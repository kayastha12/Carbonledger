import React from 'react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  currentUser,
  currentSub,
  setShowUpgradeModal,
  isDarkMode,
  setIsDarkMode,
  getAllowedTabs,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  const planTier = currentSub?.plan_tier || 'trial';
  const planMaxTokens = planTier === 'enterprise' ? 25000 : (planTier === 'professional' ? 5000 : (planTier === 'starter' ? 1000 : 100));
  const currentTokens = currentUser?.token_balance || 0;
  const tokenPct = Math.min(100, Math.max(5, (currentTokens / planMaxTokens) * 100));

  return (
    <aside style={{
      width: '270px', backgroundColor: themeCard, borderRight: `1px solid ${themeBorder}`,
      padding: '28px 18px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
      boxShadow: '4px 0 20px rgba(0,0,0,0.02)'
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
        {/* Logo Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '12px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px',
            boxShadow: '0 4px 12px rgba(16, 185, 129, 0.25)'
          }}>
            🍃
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: '800', margin: 0, letterSpacing: '-0.3px', background: 'linear-gradient(to right, #10b981, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              CarbonLedger
            </h1>
            <span style={{ fontSize: '10px', color: '#10b981', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Enterprise SaaS</span>
          </div>
        </div>

        {/* Subscription Mini Card */}
        <div style={{
          padding: '14px', borderRadius: '14px', backgroundColor: isDarkMode ? '#080c14' : '#f1f5f9',
          border: `1px solid ${themeBorder}`
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: '800', color: '#10b981', textTransform: 'uppercase' }}>
              {planTier === 'trial' ? '🌱 Free Trial' : `✨ ${planTier.toUpperCase()} PLAN`}
            </span>
            <button 
              onClick={() => setShowUpgradeModal(true)}
              style={{ background: 'none', border: 'none', fontSize: '10px', color: '#3b82f6', fontWeight: 'bold', cursor: 'pointer', padding: 0 }}>
              Upgrade
            </button>
          </div>
          <div style={{ fontSize: '12px', fontWeight: '700', color: themeText, display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span>Tokens Left:</span>
            <span style={{ color: currentTokens < 50 ? '#f87171' : '#10b981' }}>
              {currentTokens.toLocaleString()}
            </span>
          </div>
          <div style={{ height: '6px', borderRadius: '4px', backgroundColor: isDarkMode ? '#1f2937' : '#e2e8f0', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: '4px',
              width: `${tokenPct}%`,
              backgroundColor: currentTokens < 50 ? '#f87171' : '#10b981',
              transition: 'width 0.3s ease'
            }}></div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {getAllowedTabs().map(tab => (
            <button
              key={tab.name}
              onClick={() => setActiveTab(tab.name)}
              style={{
                display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px',
                borderRadius: '10px',
                backgroundColor: activeTab === tab.name ? (isDarkMode ? 'rgba(16, 185, 129, 0.12)' : 'rgba(16, 185, 129, 0.08)') : 'transparent',
                color: activeTab === tab.name ? '#10b981' : themeSubtext,
                border: 'none', cursor: 'pointer', fontSize: '13px',
                fontWeight: activeTab === tab.name ? '700' : '600', textAlign: 'left',
                transition: 'all 0.2s', transform: activeTab === tab.name ? 'translateX(4px)' : 'none'
              }}
            >
              <span style={{ fontSize: '16px' }}>{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Sidebar Footer */}
      <div style={{ borderTop: `1px solid ${themeBorder}`, paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <button 
          onClick={() => setIsDarkMode(!isDarkMode)} 
          style={{
            backgroundColor: isDarkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
            border: `1px solid ${themeBorder}`, color: themeText, padding: '8px',
            borderRadius: '8px', cursor: 'pointer', fontSize: '11px', fontWeight: '600',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
          }}>
          {isDarkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
        </button>
      </div>
    </aside>
  );
}

