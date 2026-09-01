import React from 'react';

export default function SubscriptionTab({
  currentUser,
  currentSub,
  billingHistory,
  tokenHistory,
  setShowUpgradeModal,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* Current Plan Overview Banner */}
      <div style={{
        padding: '28px', borderRadius: '18px', backgroundColor: themeCard,
        border: `1px solid ${themeBorder}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <div>
          <span style={{ fontSize: '11px', fontWeight: '800', color: '#10b981', textTransform: 'uppercase' }}>Current Subscription</span>
          <h3 style={{ fontSize: '24px', fontWeight: '800', margin: '4px 0 6px 0', color: themeText }}>
            {currentSub?.plan_tier?.toUpperCase() || 'TRIAL'} PLAN (${currentSub?.price_usd || 0}/{currentSub?.billing_cycle || 'monthly'})
          </h3>
          <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>
            Status: <strong style={{ color: currentSub?.status === 'active' ? '#10b981' : '#f59e0b' }}>{currentSub?.status?.toUpperCase() || 'TRIAL'}</strong> • Next Renewal: <strong>{currentSub?.renewal_date || '2026-12-31'}</strong> • Quota Limit: <strong>{currentSub?.report_limit === -1 ? 'Unlimited' : `${currentSub?.report_limit || 3} reports`}</strong>
          </p>
        </div>
        <button 
          onClick={() => setShowUpgradeModal(true)}
          style={{
            padding: '12px 24px', borderRadius: '10px', backgroundColor: '#10b981', color: '#080c14',
            border: 'none', fontWeight: '800', fontSize: '13px', cursor: 'pointer', boxShadow: '0 4px 12px rgba(16,185,129,0.3)'
          }}>
          Upgrade / Refill Quota
        </button>
      </div>

      {/* Invoices History Table */}
      <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
        <h4 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 16px 0', color: themeText }}>🧾 Billing History & Tax Invoices</h4>
        {!billingHistory || billingHistory.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: themeSubtext, fontSize: '12px' }}>No billing invoices generated yet.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, textTransform: 'uppercase' }}>
                  <th style={{ padding: '10px 8px' }}>Invoice ID</th>
                  <th style={{ padding: '10px 8px' }}>Plan Tier</th>
                  <th style={{ padding: '10px 8px' }}>Cycle</th>
                  <th style={{ padding: '10px 8px' }}>Amount</th>
                  <th style={{ padding: '10px 8px' }}>Invoice Date</th>
                  <th style={{ padding: '10px 8px' }}>Status</th>
                  <th style={{ padding: '10px 8px' }}>Receipt</th>
                </tr>
              </thead>
              <tbody>
                {billingHistory.map((inv, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                    <td style={{ padding: '10px 8px', fontWeight: 'bold', color: themeText }}>{inv.invoice_number}</td>
                    <td style={{ padding: '10px 8px' }}>{inv.plan_name}</td>
                    <td style={{ padding: '10px 8px', textTransform: 'capitalize' }}>{inv.billing_cycle}</td>
                    <td style={{ padding: '10px 8px', fontWeight: 'bold', color: '#10b981' }}>${inv.amount_usd}</td>
                    <td style={{ padding: '10px 8px', color: themeSubtext }}>{inv.invoice_date}</td>
                    <td style={{ padding: '10px 8px' }}>
                      <span style={{ backgroundColor: 'rgba(16,185,129,0.15)', color: '#10b981', padding: '3px 8px', borderRadius: '4px', fontWeight: 'bold', fontSize: '11px' }}>
                        {inv.payment_status}
                      </span>
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      <span style={{ color: '#3b82f6', cursor: 'pointer', fontWeight: 'bold' }}>Download PDF</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Token Transactions Ledger */}
      <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
        <h4 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 16px 0', color: themeText }}>⚡ Token Consumption Ledger</h4>
        {!tokenHistory || tokenHistory.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: themeSubtext, fontSize: '12px' }}>No token transactions recorded yet.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, textTransform: 'uppercase' }}>
                  <th style={{ padding: '10px 8px' }}>Timestamp</th>
                  <th style={{ padding: '10px 8px' }}>Action</th>
                  <th style={{ padding: '10px 8px' }}>Tokens</th>
                  <th style={{ padding: '10px 8px' }}>Balance After</th>
                  <th style={{ padding: '10px 8px' }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {tokenHistory.map((tx, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                    <td style={{ padding: '10px 8px', color: themeSubtext }}>{tx.timestamp}</td>
                    <td style={{ padding: '10px 8px', fontWeight: 'bold', color: themeText }}>{tx.action_type}</td>
                    <td style={{ padding: '10px 8px', fontWeight: 'bold', color: tx.amount < 0 ? '#f87171' : '#10b981' }}>
                      {tx.amount > 0 ? `+${tx.amount}` : tx.amount}
                    </td>
                    <td style={{ padding: '10px 8px', fontWeight: 'bold' }}>{(tx.balance_after || 0).toLocaleString()}</td>
                    <td style={{ padding: '10px 8px', color: themeSubtext }}>{tx.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}

