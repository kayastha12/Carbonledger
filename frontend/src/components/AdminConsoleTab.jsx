import React from 'react';

export default function AdminConsoleTab({
  adminSubTab,
  setAdminSubTab,
  adminStats,
  adminUsersList,
  adminUserSearch,
  setAdminUserSearch,
  adminRules,
  adminFactors,
  adminAuditLogs,
  currentUser,
  setSelectedAdminUser,
  setShowAdjustTokensModal,
  setSubOverridePlan,
  setShowOverrideSubModal,
  handleAdminToggleUser,
  handleAdminDeleteUser,
  fetchAdminData,
  showToast,
  getAuthHeaders,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Admin Sub Navigation */}
      <div style={{ display: 'flex', gap: '8px', backgroundColor: themeCard, padding: '6px', borderRadius: '12px', border: `1px solid ${themeBorder}`, flexWrap: 'wrap' }}>
        {[
          { id: 'overview', label: '📊 SaaS Overview & MRR' },
          { id: 'users', label: '👥 User & Token Management' },
          { id: 'rules', label: '⚙️ Calculation Rules' },
          { id: 'factors', label: '🏷️ Factor Overrides' },
          { id: 'audit', label: '📜 Audit Trail' }
        ].map(st => (
          <button
            key={st.id} onClick={() => setAdminSubTab(st.id)}
            style={{
              padding: '9px 16px', borderRadius: '8px', border: 'none',
              backgroundColor: adminSubTab === st.id ? '#10b981' : 'transparent',
              color: adminSubTab === st.id ? '#080c14' : themeSubtext,
              fontWeight: 'bold', cursor: 'pointer', fontSize: '12px'
            }}>
            {st.label}
          </button>
        ))}
      </div>

      {/* 1. ADMIN OVERVIEW & MRR */}
      {adminSubTab === 'overview' && adminStats && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '14px' }}>
            {[
              { label: 'Total Users', val: adminStats.total_users, sub: 'Registered Accounts', color: '#3b82f6' },
              { label: 'Active Users', val: adminStats.active_users, sub: 'Unrestricted', color: '#10b981' },
              { label: 'Free Trial Users', val: adminStats.trial_users, sub: 'Trial Quota', color: '#f59e0b' },
              { label: 'Paid Subscribers', val: adminStats.paid_subscribers, sub: 'Active Plans', color: '#8b5cf6' },
              { label: 'Monthly Revenue (MRR)', val: `$${(adminStats.monthly_revenue_usd || 0).toLocaleString()}`, sub: 'Recurring Billing', color: '#10b981' },
              { label: 'Total Tokens Consumed', val: (adminStats.total_tokens_consumed || 0).toLocaleString(), sub: 'Platform Volume', color: '#06b6d4' }
            ].map((st, i) => (
              <div key={i} style={{ padding: '20px', borderRadius: '14px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
                <div style={{ fontSize: '11px', color: themeSubtext, fontWeight: '700', textTransform: 'uppercase' }}>{st.label}</div>
                <div style={{ fontSize: '22px', fontWeight: '800', color: st.color, margin: '4px 0' }}>{st.val}</div>
                <div style={{ fontSize: '11px', color: themeSubtext }}>{st.sub}</div>
              </div>
            ))}
          </div>

          <div style={{ padding: '20px', borderRadius: '16px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
            <h4 style={{ fontSize: '14px', fontWeight: '800', margin: '0 0 12px 0', color: themeText }}>🖥️ System & Infrastructure Health</h4>
            <div style={{ display: 'flex', gap: '24px', fontSize: '13px' }}>
              <div>Database: <strong style={{ color: '#10b981' }}>{adminStats.system_health?.database_status || 'Operational (SQLite Multi-tenant)'}</strong></div>
              <div>OCR Engine: <strong style={{ color: '#10b981' }}>{adminStats.system_health?.ocr_engine_status || 'Online (Tesseract+LLM)'}</strong></div>
              <div>API Latency: <strong>{adminStats.system_health?.api_latency_ms || 12} ms</strong></div>
            </div>
          </div>
        </div>
      )}

      {/* 2. ADMIN USER & TOKEN MANAGEMENT */}
      {adminSubTab === 'users' && (
        <div style={{ padding: '24px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '800', margin: 0, color: themeText }}>👥 Enterprise User Governance ({adminUsersList.length})</h3>
              <p style={{ fontSize: '12px', color: themeSubtext, margin: '2px 0 0' }}>Manage accounts, adjust token allocations, and override plan subscriptions</p>
            </div>
            <input 
              type="text" placeholder="Search user, email, organization..."
              value={adminUserSearch} onChange={e => setAdminUserSearch(e.target.value)}
              style={{ padding: '9px 14px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '12px', width: '280px', outline: 'none' }}
            />
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, textTransform: 'uppercase' }}>
                  <th style={{ padding: '10px 8px' }}>User</th>
                  <th style={{ padding: '10px 8px' }}>Organization</th>
                  <th style={{ padding: '10px 8px' }}>Plan</th>
                  <th style={{ padding: '10px 8px' }}>Tokens</th>
                  <th style={{ padding: '10px 8px' }}>Status</th>
                  <th style={{ padding: '10px 8px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {adminUsersList
                  .filter(u => !adminUserSearch || u.email?.toLowerCase().includes(adminUserSearch.toLowerCase()) || u.full_name?.toLowerCase().includes(adminUserSearch.toLowerCase()) || u.organization?.toLowerCase().includes(adminUserSearch.toLowerCase()))
                  .map(u => (
                    <tr key={u.id} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                      <td style={{ padding: '10px 8px' }}>
                        <div style={{ fontWeight: 'bold', color: themeText }}>{u.full_name}</div>
                        <div style={{ fontSize: '11px', color: themeSubtext }}>{u.email}</div>
                      </td>
                      <td style={{ padding: '10px 8px' }}>{u.organization || 'N/A'}</td>
                      <td style={{ padding: '10px 8px' }}>
                        <span style={{ padding: '3px 8px', borderRadius: '4px', backgroundColor: 'rgba(59,130,246,0.15)', color: '#60a5fa', fontWeight: 'bold', textTransform: 'uppercase', fontSize: '10px' }}>
                          {u.plan_tier || 'Trial'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 8px', fontWeight: 'bold', color: '#10b981' }}>{(u.token_balance || 0).toLocaleString()}</td>
                      <td style={{ padding: '10px 8px' }}>
                        <span style={{ color: u.is_active ? '#10b981' : '#f87171', fontWeight: 'bold' }}>
                          {u.is_active ? '● Active' : '○ Suspended'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 8px', display: 'flex', gap: '6px' }}>
                        <button 
                          onClick={() => { setSelectedAdminUser(u); setShowAdjustTokensModal(true); }}
                          style={{ padding: '5px 10px', borderRadius: '6px', border: '1px solid #10b981', background: 'rgba(16,185,129,0.1)', color: '#34d399', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}>
                          ⚡ Tokens
                        </button>
                        <button 
                          onClick={() => { setSelectedAdminUser(u); setSubOverridePlan(u.plan_tier || 'starter'); setShowOverrideSubModal(true); }}
                          style={{ padding: '5px 10px', borderRadius: '6px', border: '1px solid #3b82f6', background: 'rgba(59,130,246,0.1)', color: '#60a5fa', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}>
                          💳 Plan
                        </button>
                        <button 
                          onClick={() => handleAdminToggleUser(u.id)}
                          style={{ padding: '5px 10px', borderRadius: '6px', border: '1px solid #f59e0b', background: 'rgba(245,158,11,0.1)', color: '#fbbf24', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}>
                          {u.is_active ? 'Suspend' : 'Activate'}
                        </button>
                        {u.id !== currentUser.id && (
                          <button 
                            onClick={() => handleAdminDeleteUser(u.id)}
                            style={{ padding: '5px 10px', borderRadius: '6px', border: '1px solid #ef4444', background: 'rgba(239,68,68,0.1)', color: '#f87171', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}>
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. CALCULATION RULES SUB-TAB */}
      {adminSubTab === 'rules' && (
        <div style={{ padding: '24px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
          <h3 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 16px 0', color: '#10b981' }}>📋 Calculation Engine Dynamic Rules ({adminRules.length})</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, textTransform: 'uppercase' }}>
                <th style={{ padding: '8px' }}>Priority</th>
                <th style={{ padding: '8px' }}>Rule Name</th>
                <th style={{ padding: '8px' }}>Condition</th>
                <th style={{ padding: '8px' }}>Target Action</th>
                <th style={{ padding: '8px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {adminRules.map(r => (
                <tr key={r.id} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                  <td style={{ padding: '8px', fontWeight: 'bold', color: '#10b981' }}>#{r.priority}</td>
                  <td style={{ padding: '8px', fontWeight: 'bold', color: themeText }}>{r.rule_name}</td>
                  <td style={{ padding: '8px' }}><code>{r.condition_field}</code> {r.condition_operator} "{r.condition_value}"</td>
                  <td style={{ padding: '8px', color: '#3b82f6', fontWeight: 'bold' }}>{r.target_action} ➔ {r.target_value}</td>
                  <td style={{ padding: '8px' }}>
                    <button 
                      onClick={() => {
                        fetch(`http://localhost:8000/api/v1/admin/rules/${r.id}`, { method: 'DELETE', headers: getAuthHeaders() })
                          .then(() => { showToast('Rule removed'); fetchAdminData(); });
                      }}
                      style={{ padding: '3px 8px', borderRadius: '4px', border: '1px solid #ef4444', background: 'rgba(239,68,68,0.1)', color: '#f87171', cursor: 'pointer', fontSize: '10px' }}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 4. FACTOR OVERRIDES SUB-TAB */}
      {adminSubTab === 'factors' && (
        <div style={{ padding: '24px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
          <h3 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 16px 0', color: '#10b981' }}>🏷️ Custom Emission Factor Overrides ({adminFactors.length})</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, textTransform: 'uppercase' }}>
                <th style={{ padding: '8px' }}>Material Pattern</th>
                <th style={{ padding: '8px' }}>Region</th>
                <th style={{ padding: '8px' }}>Scope</th>
                <th style={{ padding: '8px' }}>Factor</th>
                <th style={{ padding: '8px' }}>Source Certification</th>
              </tr>
            </thead>
            <tbody>
              {adminFactors.map(f => (
                <tr key={f.id} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                  <td style={{ padding: '8px', fontWeight: 'bold', color: themeText }}>{f.material_pattern}</td>
                  <td style={{ padding: '8px' }}>{f.region}</td>
                  <td style={{ padding: '8px' }}>{f.scope}</td>
                  <td style={{ padding: '8px', color: '#10b981', fontWeight: 'bold' }}>{f.custom_emission_factor} kg CO₂e/{f.unit}</td>
                  <td style={{ padding: '8px', color: themeSubtext }}>{f.source_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 5. AUDIT TRAIL SUB-TAB */}
      {adminSubTab === 'audit' && (
        <div style={{ padding: '24px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
          <h3 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 16px 0', color: '#10b981' }}>📜 Administrative Audit Trail</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, textTransform: 'uppercase' }}>
                <th style={{ padding: '8px' }}>Timestamp</th>
                <th style={{ padding: '8px' }}>Admin</th>
                <th style={{ padding: '8px' }}>Action</th>
                <th style={{ padding: '8px' }}>Module</th>
                <th style={{ padding: '8px' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {adminAuditLogs.map(a => (
                <tr key={a.id} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                  <td style={{ padding: '8px', color: themeSubtext }}>{a.timestamp}</td>
                  <td style={{ padding: '8px', fontWeight: 'bold', color: themeText }}>{a.user_email}</td>
                  <td style={{ padding: '8px' }}><span style={{ backgroundColor: 'rgba(16,185,129,0.15)', color: '#10b981', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>{a.action_type}</span></td>
                  <td style={{ padding: '8px' }}>{a.target_module}</td>
                  <td style={{ padding: '8px', color: themeText }}>{a.new_value || a.old_value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

    </div>
  );
}

