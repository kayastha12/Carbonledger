import React from 'react';

export default function UpgradeModal({
  showUpgradeModal,
  setShowUpgradeModal,
  currentSub,
  billingCycle,
  setBillingCycle,
  plans,
  handleUpgradePlan,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  if (!showUpgradeModal) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 999,
      backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
    }}>
      <div style={{
        width: '100%', maxWidth: '960px', maxHeight: '90vh', overflowY: 'auto',
        backgroundColor: themeCard, borderRadius: '24px', border: `1px solid ${themeBorder}`,
        padding: '36px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h3 style={{ fontSize: '24px', fontWeight: '800', margin: 0, color: '#10b981' }}>✨ Upgrade Your CarbonLedger Workspace</h3>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: themeSubtext }}>Choose the plan tailored for your enterprise ESG & CBAM reporting compliance</p>
          </div>
          <button onClick={() => setShowUpgradeModal(false)} style={{ background: 'none', border: 'none', fontSize: '22px', color: themeSubtext, cursor: 'pointer' }}>✕</button>
        </div>

        {/* Monthly / Yearly Toggle */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '28px' }}>
          <div style={{ display: 'inline-flex', backgroundColor: isDarkMode ? '#080c14' : '#f1f5f9', padding: '4px', borderRadius: '12px', border: `1px solid ${themeBorder}` }}>
            <button 
              onClick={() => setBillingCycle('monthly')}
              style={{ padding: '8px 20px', borderRadius: '8px', border: 'none', backgroundColor: billingCycle === 'monthly' ? '#10b981' : 'transparent', color: billingCycle === 'monthly' ? '#080c14' : themeSubtext, fontWeight: 'bold', cursor: 'pointer', fontSize: '13px' }}>
              Monthly Billing
            </button>
            <button 
              onClick={() => setBillingCycle('yearly')}
              style={{ padding: '8px 20px', borderRadius: '8px', border: 'none', backgroundColor: billingCycle === 'yearly' ? '#10b981' : 'transparent', color: billingCycle === 'yearly' ? '#080c14' : themeSubtext, fontWeight: 'bold', cursor: 'pointer', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>Yearly Billing</span>
              <span style={{ fontSize: '10px', backgroundColor: '#3b82f6', color: '#fff', padding: '2px 6px', borderRadius: '10px' }}>20% OFF</span>
            </button>
          </div>
        </div>

        {/* Pricing Cards Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '16px' }}>
          {plans.map(p => {
            const isCurrent = currentSub.plan_tier === p.key;
            const price = billingCycle === 'yearly' ? p.yearly_price : p.monthly_price;
            return (
              <div key={p.key} style={{
                padding: '24px', borderRadius: '16px', backgroundColor: isDarkMode ? '#080c14' : '#ffffff',
                border: `1px solid ${p.popular ? '#10b981' : themeBorder}`, position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'
              }}>
                {p.popular && (
                  <div style={{ position: 'absolute', top: '-12px', right: '16px', backgroundColor: '#10b981', color: '#080c14', fontSize: '10px', fontWeight: '800', padding: '4px 10px', borderRadius: '10px' }}>
                    ⭐ MOST POPULAR
                  </div>
                )}
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 8px 0' }}>{p.name}</h4>
                  <div style={{ marginBottom: '16px' }}>
                    <span style={{ fontSize: '28px', fontWeight: '800', color: themeText }}>${price}</span>
                    <span style={{ fontSize: '12px', color: themeSubtext }}>/{billingCycle === 'yearly' ? 'yr' : 'mo'}</span>
                  </div>
                  <div style={{ padding: '8px 10px', borderRadius: '8px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', fontSize: '12px', fontWeight: 'bold', marginBottom: '16px' }}>
                    ⚡ {p.tokens.toLocaleString()} Tokens / mo
                  </div>
                  <ul style={{ padding: 0, margin: '0 0 20px 0', listStyle: 'none', fontSize: '12px', color: themeSubtext, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {p.features.map((f, i) => (
                      <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ color: '#10b981' }}>✓</span> {f}
                      </li>
                    ))}
                  </ul>
                </div>

                <button 
                  disabled={isCurrent}
                  onClick={() => handleUpgradePlan(p.key, billingCycle)}
                  style={{
                    width: '100%', padding: '10px', borderRadius: '8px', border: 'none',
                    backgroundColor: isCurrent ? 'rgba(255,255,255,0.05)' : (p.popular ? '#10b981' : '#3b82f6'),
                    color: isCurrent ? themeSubtext : (p.popular ? '#080c14' : '#ffffff'),
                    fontWeight: 'bold', fontSize: '13px', cursor: isCurrent ? 'default' : 'pointer'
                  }}>
                  {isCurrent ? 'Current Plan' : (p.key === 'trial' ? 'Free' : '1-Click Upgrade')}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

