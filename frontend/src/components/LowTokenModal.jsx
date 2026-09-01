import React from 'react';

export default function LowTokenModal({
  showLowTokenModal,
  setShowLowTokenModal,
  setShowUpgradeModal,
  lowTokenDetails,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  if (!showLowTokenModal) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1000,
      backgroundColor: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
    }}>
      <div style={{
        width: '100%', maxWidth: '420px', backgroundColor: themeCard,
        borderRadius: '20px', border: `1px solid ${themeBorder}`,
        padding: '30px', textAlign: 'center',
        boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
      }}>
        <div style={{ fontSize: '44px', marginBottom: '12px' }}>⚡</div>
        <h3 style={{ fontSize: '20px', fontWeight: '800', margin: '0 0 8px 0', color: '#f87171' }}>
          Insufficient Token Balance
        </h3>
        <p style={{ fontSize: '13px', color: themeSubtext, margin: '0 0 20px 0', lineHeight: 1.5 }}>
          This operation requires <strong style={{ color: themeText }}>{lowTokenDetails.required} tokens</strong>, but your account only has <strong style={{ color: '#f87171' }}>{lowTokenDetails.current} tokens</strong> left. Upgrade your plan to instantly refill your token quota.
        </p>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => setShowLowTokenModal(false)}
            style={{
              flex: 1, padding: '10px', borderRadius: '8px', border: `1px solid ${themeBorder}`,
              background: 'transparent', color: themeText, fontWeight: 'bold', cursor: 'pointer', fontSize: '13px'
            }}>
            Cancel
          </button>
          <button 
            onClick={() => { setShowLowTokenModal(false); setShowUpgradeModal(true); }}
            style={{
              flex: 1, padding: '10px', borderRadius: '8px', border: 'none',
              background: '#10b981', color: '#080c14', fontWeight: '800', cursor: 'pointer', fontSize: '13px',
              boxShadow: '0 4px 12px rgba(16,185,129,0.3)'
            }}>
            Upgrade Plan
          </button>
        </div>
      </div>
    </div>
  );
}

