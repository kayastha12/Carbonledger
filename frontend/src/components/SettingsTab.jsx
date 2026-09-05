import React from 'react';
import { API_BASE } from '../config';

export default function SettingsTab({
  currentUser,
  setCurrentUser,
  getAuthHeaders,
  showToast,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  const handleSaveProfile = () => {
    fetch(`${API_BASE}/api/v1/user/profile`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        full_name: currentUser.full_name,
        organization: currentUser.organization,
        default_region: currentUser.default_region
      })
    })
    .then(res => res.json())
    .then(() => {
      localStorage.setItem('carbonledger_user', JSON.stringify(currentUser));
      showToast('Profile preferences updated successfully!');
    })
    .catch(() => showToast('Failed to update profile.'));
  };

  return (
    <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}`, maxWidth: '640px' }}>
      <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 8px 0', color: '#10b981' }}>
        ⚙️ Enterprise Account Settings
      </h3>
      <p style={{ fontSize: '12px', color: themeSubtext, margin: '0 0 20px 0' }}>
        Manage tenant organizational metadata, default benchmark regions, and team preferences.
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px', color: themeText }}>Full Name</label>
          <input 
            type="text" value={currentUser?.full_name || ''} 
            onChange={e => setCurrentUser({ ...currentUser, full_name: e.target.value })}
            style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px', color: themeText }}>Organization / Legal Entity</label>
          <input 
            type="text" value={currentUser?.organization || ''} 
            onChange={e => setCurrentUser({ ...currentUser, organization: e.target.value })}
            style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px', color: themeText }}>Corporate Email (Read Only)</label>
          <input 
            type="email" disabled value={currentUser?.email || ''} 
            style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#1f2937' : '#f1f5f9', color: themeSubtext, fontSize: '13px', cursor: 'not-allowed' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px', color: themeText }}>Default Carbon Accounting Region</label>
          <select 
            value={currentUser?.default_region || 'DE'} 
            onChange={e => setCurrentUser({ ...currentUser, default_region: e.target.value })}
            style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}>
            <option value="DE">Germany (DE) - EU Grid Benchmark</option>
            <option value="IN">India (IN) - CEA National Grid</option>
            <option value="US">United States (US) - eGRID National Avg</option>
            <option value="FR">France (FR) - Nuclear Low Carbon Grid</option>
            <option value="GB">United Kingdom (GB) - DESNZ Standard</option>
          </select>
        </div>

        <button 
          onClick={handleSaveProfile}
          style={{
            padding: '12px', borderRadius: '8px', backgroundColor: '#10b981', color: '#080c14',
            border: 'none', fontWeight: '800', fontSize: '13px', cursor: 'pointer', marginTop: '10px',
            boxShadow: '0 4px 12px rgba(16,185,129,0.3)'
          }}>
          Save Account Preferences
        </button>
      </div>
    </div>
  );
}

