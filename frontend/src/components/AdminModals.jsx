import React from 'react';

export default function AdminModals({
  showAdjustTokensModal,
  setShowAdjustTokensModal,
  selectedAdminUser,
  tokenAdjustType,
  setTokenAdjustType,
  tokenAdjustAmount,
  setTokenAdjustAmount,
  tokenAdjustReason,
  setTokenAdjustReason,
  handleAdminAdjustTokens,
  showOverrideSubModal,
  setShowOverrideSubModal,
  subOverridePlan,
  setSubOverridePlan,
  subOverrideCycle,
  setSubOverrideCycle,
  subOverrideStatus,
  setSubOverrideStatus,
  handleAdminOverrideSub,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  return (
    <>
      {/* ADMIN ADJUST TOKENS MODAL */}
      {showAdjustTokensModal && selectedAdminUser && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1000,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
        }}>
          <div style={{
            width: '100%', maxWidth: '440px', backgroundColor: themeCard,
            borderRadius: '20px', border: `1px solid ${themeBorder}`,
            padding: '30px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 4px 0', color: '#10b981' }}>
              ⚡ Adjust Tokens for {selectedAdminUser.full_name}
            </h3>
            <p style={{ fontSize: '12px', color: themeSubtext, margin: '0 0 16px 0' }}>
              Current Balance: <strong style={{ color: '#10b981' }}>{(selectedAdminUser.token_balance || 0).toLocaleString()} tokens</strong>
            </p>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Operation</label>
              <select 
                value={tokenAdjustType} onChange={e => setTokenAdjustType(e.target.value)} 
                style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}>
                <option value="add">Add Tokens (+)</option>
                <option value="subtract">Subtract Tokens (-)</option>
                <option value="set">Set Exact Balance (=)</option>
              </select>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Amount</label>
              <input 
                type="number" value={tokenAdjustAmount} onChange={e => setTokenAdjustAmount(parseInt(e.target.value) || 0)} 
                style={{ width: '100%', boxSizing: 'border-box', padding: '9px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }} 
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Audit Reason (Required)</label>
              <input 
                type="text" value={tokenAdjustReason} onChange={e => setTokenAdjustReason(e.target.value)} 
                placeholder="e.g. Customer Support Goodwill Bonus" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '9px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }} 
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                onClick={() => setShowAdjustTokensModal(false)} 
                style={{ flex: 1, padding: '10px', borderRadius: '8px', border: `1px solid ${themeBorder}`, background: 'transparent', color: themeText, cursor: 'pointer', fontWeight: 'bold', fontSize: '13px' }}>
                Cancel
              </button>
              <button 
                onClick={handleAdminAdjustTokens} 
                style={{ flex: 1, padding: '10px', borderRadius: '8px', border: 'none', background: '#10b981', color: '#080c14', cursor: 'pointer', fontWeight: '800', fontSize: '13px' }}>
                Save Tokens
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ADMIN OVERRIDE SUBSCRIPTION MODAL */}
      {showOverrideSubModal && selectedAdminUser && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1000,
          backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
        }}>
          <div style={{
            width: '100%', maxWidth: '440px', backgroundColor: themeCard,
            borderRadius: '20px', border: `1px solid ${themeBorder}`,
            padding: '30px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 4px 0', color: '#3b82f6' }}>
              💳 Plan Control for {selectedAdminUser.full_name}
            </h3>
            <p style={{ fontSize: '12px', color: themeSubtext, margin: '0 0 16px 0' }}>
              Assign promotional plan tiers or modify subscription status
            </p>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Plan Tier</label>
              <select 
                value={subOverridePlan} onChange={e => setSubOverridePlan(e.target.value)} 
                style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}>
                <option value="trial">Free Trial (100 Tokens)</option>
                <option value="starter">Starter Plan ($49/mo - 1,000 Tokens)</option>
                <option value="professional">Professional Plan ($149/mo - 5,000 Tokens)</option>
                <option value="enterprise">Enterprise Plan ($499/mo - 25,000 Tokens)</option>
              </select>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Billing Cycle</label>
              <select 
                value={subOverrideCycle} onChange={e => setSubOverrideCycle(e.target.value)} 
                style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Subscription Status</label>
              <select 
                value={subOverrideStatus} onChange={e => setSubOverrideStatus(e.target.value)} 
                style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}>
                <option value="active">Active</option>
                <option value="trial">Trial</option>
                <option value="cancelled">Cancelled</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                onClick={() => setShowOverrideSubModal(false)} 
                style={{ flex: 1, padding: '10px', borderRadius: '8px', border: `1px solid ${themeBorder}`, background: 'transparent', color: themeText, cursor: 'pointer', fontWeight: 'bold', fontSize: '13px' }}>
                Cancel
              </button>
              <button 
                onClick={handleAdminOverrideSub} 
                style={{ flex: 1, padding: '10px', borderRadius: '8px', border: 'none', background: '#3b82f6', color: '#ffffff', cursor: 'pointer', fontWeight: '800', fontSize: '13px' }}>
                Save Override
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

