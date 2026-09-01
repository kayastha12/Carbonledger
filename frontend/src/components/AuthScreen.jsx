import React, { useState } from 'react';

export default function AuthScreen({ onLoginSuccess, isDarkMode, themeText, themeSubtext, themeBorder, themeCard }) {
  const [authMode, setAuthMode] = useState('login'); // 'login', 'signup', 'forgot', 'reset'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [organization, setOrganization] = useState('');
  const [defaultRegion, setDefaultRegion] = useState('DE');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.trim(), password })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      setIsLoading(false);
      if (status !== 200) throw new Error(body.detail || 'Login failed. Please check your credentials.');
      localStorage.setItem('carbonledger_token', body.token);
      localStorage.setItem('carbonledger_user', JSON.stringify(body.user));
      if (body.subscription) localStorage.setItem('carbonledger_sub', JSON.stringify(body.subscription));
      onLoginSuccess(body.user, body.subscription);
    })
    .catch(err => {
      setIsLoading(false);
      setErrorMsg(err.message);
    });
  };

  const handleRegister = (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        organization: organization.trim(),
        default_region: defaultRegion,
        role: 'subscriber'
      })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      setIsLoading(false);
      if (status !== 200) throw new Error(body.detail || 'Registration failed.');
      localStorage.setItem('carbonledger_token', body.token);
      localStorage.setItem('carbonledger_user', JSON.stringify(body.user));
      if (body.subscription) localStorage.setItem('carbonledger_sub', JSON.stringify(body.subscription));
      onLoginSuccess(body.user, body.subscription);
    })
    .catch(err => {
      setIsLoading(false);
      setErrorMsg(err.message);
    });
  };

  const handleForgotPassword = (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    fetch('http://localhost:8000/api/v1/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.trim() })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      setIsLoading(false);
      if (status !== 200) throw new Error(body.detail || 'Unable to process request.');
      setSuccessMsg(`Reset code generated: ${body.reset_code || 'Sent to email'}. Please enter below.`);
      if (body.reset_code) setResetToken(body.reset_code);
      setAuthMode('reset');
    })
    .catch(err => {
      setIsLoading(false);
      setErrorMsg(err.message);
    });
  };

  const handleResetPassword = (e) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    fetch('http://localhost:8000/api/v1/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.trim(),
        reset_token: resetToken.trim(),
        new_password: newPassword
      })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      setIsLoading(false);
      if (status !== 200) throw new Error(body.detail || 'Password reset failed.');
      setSuccessMsg('Password updated successfully! Please sign in with your new password.');
      setAuthMode('login');
      setPassword('');
    })
    .catch(err => {
      setIsLoading(false);
      setErrorMsg(err.message);
    });
  };

  const handleQuickDemoLogin = (demoEmail, demoPw) => {
    setEmail(demoEmail);
    setPassword(demoPw);
    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: demoEmail, password: demoPw })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      setIsLoading(false);
      if (status !== 200) throw new Error(body.detail || 'Login failed.');
      localStorage.setItem('carbonledger_token', body.token);
      localStorage.setItem('carbonledger_user', JSON.stringify(body.user));
      if (body.subscription) localStorage.setItem('carbonledger_sub', JSON.stringify(body.subscription));
      onLoginSuccess(body.user, body.subscription);
    })
    .catch(err => {
      setIsLoading(false);
      setErrorMsg(err.message);
    });
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: isDarkMode ? '#080c14' : '#f1f5f9',
      fontFamily: 'Outfit, Inter, sans-serif',
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '440px',
        padding: '36px',
        borderRadius: '20px',
        backgroundColor: isDarkMode ? '#111827' : '#ffffff',
        border: `1px solid ${themeBorder}`,
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '14px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            marginBottom: '10px',
            boxShadow: '0 8px 16px rgba(16, 185, 129, 0.25)'
          }}>
            🍃
          </div>
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '800', letterSpacing: '-0.5px', color: '#10b981' }}>
            CarbonLedger OS
          </h2>
          <p style={{ margin: '6px 0 0', fontSize: '13px', color: themeSubtext }}>
            {authMode === 'login' && 'Sign in to access your carbon accounting platform'}
            {authMode === 'signup' && 'Create your enterprise workspace (100 Free Tokens)'}
            {authMode === 'forgot' && 'Reset your CarbonLedger account password'}
            {authMode === 'reset' && 'Enter your 6-digit code and set new password'}
          </p>
        </div>

        {/* Notifications */}
        {errorMsg && (
          <div style={{ padding: '10px 14px', borderRadius: '10px', backgroundColor: 'rgba(239,68,68,0.12)', border: '1px solid #ef4444', color: '#f87171', fontSize: '12px', marginBottom: '16px', fontWeight: '600' }}>
            ⚠️ {errorMsg}
          </div>
        )}
        {successMsg && (
          <div style={{ padding: '10px 14px', borderRadius: '10px', backgroundColor: 'rgba(16,185,129,0.12)', border: '1px solid #10b981', color: '#34d399', fontSize: '12px', marginBottom: '16px', fontWeight: '600' }}>
            ✅ {successMsg}
          </div>
        )}

        {/* Auth Mode Tabs */}
        {(authMode === 'login' || authMode === 'signup') && (
          <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', backgroundColor: isDarkMode ? '#1f2937' : '#f1f5f9', padding: '4px', borderRadius: '10px' }}>
            <button 
              onClick={() => { setAuthMode('login'); setErrorMsg(''); }} 
              style={{
                flex: 1, padding: '9px', borderRadius: '8px', border: 'none',
                backgroundColor: authMode === 'login' ? '#10b981' : 'transparent',
                color: authMode === 'login' ? '#080c14' : themeSubtext,
                fontWeight: 'bold', cursor: 'pointer', fontSize: '13px', transition: 'all 0.2s'
              }}>
              Sign In
            </button>
            <button 
              onClick={() => { setAuthMode('signup'); setErrorMsg(''); }} 
              style={{
                flex: 1, padding: '9px', borderRadius: '8px', border: 'none',
                backgroundColor: authMode === 'signup' ? '#10b981' : 'transparent',
                color: authMode === 'signup' ? '#080c14' : themeSubtext,
                fontWeight: 'bold', cursor: 'pointer', fontSize: '13px', transition: 'all 0.2s'
              }}>
              Sign Up
            </button>
          </div>
        )}

        {/* SIGN IN FORM */}
        {authMode === 'login' && (
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '6px', color: themeText }}>Corporate Email</label>
              <input 
                type="email" 
                required
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                placeholder="name@company.com" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '11px 14px', borderRadius: '10px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px', outline: 'none' }} 
              />
            </div>

            <div style={{ marginBottom: '18px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ fontSize: '12px', fontWeight: '700', color: themeText }}>Password</label>
                <span 
                  onClick={() => { setAuthMode('forgot'); setErrorMsg(''); setSuccessMsg(''); }}
                  style={{ fontSize: '11px', color: '#10b981', cursor: 'pointer', fontWeight: '600' }}>
                  Forgot password?
                </span>
              </div>
              <input 
                type="password" 
                required
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                placeholder="••••••••" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '11px 14px', borderRadius: '10px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px', outline: 'none' }} 
              />
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: 'none', backgroundColor: '#10b981', color: '#080c14', fontWeight: '800', fontSize: '14px', cursor: 'pointer', boxShadow: '0 4px 12px rgba(16,185,129,0.3)' }}>
              {isLoading ? 'Signing In...' : 'Sign In to Workspace'}
            </button>
          </form>
        )}

        {/* SIGN UP FORM */}
        {authMode === 'signup' && (
          <form onSubmit={handleRegister}>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px', color: themeText }}>Full Name</label>
              <input 
                type="text" 
                required
                value={fullName} 
                onChange={e => setFullName(e.target.value)} 
                placeholder="Dr. Emily Watson" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
              />
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px', color: themeText }}>Organization Name</label>
              <input 
                type="text" 
                required
                value={organization} 
                onChange={e => setOrganization(e.target.value)} 
                placeholder="Siemens Energy ESG" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '10px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px', color: themeText }}>Corporate Email</label>
                <input 
                  type="email" 
                  required
                  value={email} 
                  onChange={e => setEmail(e.target.value)} 
                  placeholder="emily@siemens.com" 
                  style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px', color: themeText }}>Region</label>
                <select 
                  value={defaultRegion}
                  onChange={e => setDefaultRegion(e.target.value)}
                  style={{ width: '100%', boxSizing: 'border-box', padding: '10px 8px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }}>
                  <option value="DE">DE (EU)</option>
                  <option value="IN">IN (Asia)</option>
                  <option value="US">US (Americas)</option>
                  <option value="FR">FR (EU)</option>
                  <option value="GB">UK (GB)</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px', color: themeText }}>Create Password</label>
              <input 
                type="password" 
                required
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                placeholder="••••••••" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
              />
            </div>

            <button 
              type="submit" 
              disabled={isLoading}
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: 'none', backgroundColor: '#10b981', color: '#080c14', fontWeight: '800', fontSize: '14px', cursor: 'pointer', boxShadow: '0 4px 12px rgba(16,185,129,0.3)' }}>
              {isLoading ? 'Creating Account...' : 'Start Free Trial (100 Tokens)'}
            </button>
          </form>
        )}

        {/* FORGOT PASSWORD FORM */}
        {authMode === 'forgot' && (
          <form onSubmit={handleForgotPassword}>
            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '6px', color: themeText }}>Account Email</label>
              <input 
                type="email" 
                required
                value={email} 
                onChange={e => setEmail(e.target.value)} 
                placeholder="name@company.com" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '11px 14px', borderRadius: '10px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
              />
            </div>
            <button 
              type="submit" 
              disabled={isLoading}
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: 'none', backgroundColor: '#10b981', color: '#080c14', fontWeight: '800', fontSize: '14px', cursor: 'pointer', marginBottom: '12px' }}>
              {isLoading ? 'Sending Code...' : 'Send Verification Code'}
            </button>
            <div style={{ textAlign: 'center' }}>
              <button 
                type="button"
                onClick={() => setAuthMode('login')} 
                style={{ background: 'none', border: 'none', color: themeSubtext, fontSize: '12px', cursor: 'pointer', fontWeight: '600' }}>
                ← Back to Sign In
              </button>
            </div>
          </form>
        )}

        {/* RESET PASSWORD FORM */}
        {authMode === 'reset' && (
          <form onSubmit={handleResetPassword}>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px', color: themeText }}>Verification Code</label>
              <input 
                type="text" 
                required
                value={resetToken} 
                onChange={e => setResetToken(e.target.value)} 
                placeholder="e.g. 849201" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px', letterSpacing: '2px', fontWeight: 'bold' }} 
              />
            </div>
            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px', color: themeText }}>New Password</label>
              <input 
                type="password" 
                required
                value={newPassword} 
                onChange={e => setNewPassword(e.target.value)} 
                placeholder="••••••••" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
              />
            </div>
            <button 
              type="submit" 
              disabled={isLoading}
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: 'none', backgroundColor: '#10b981', color: '#080c14', fontWeight: '800', fontSize: '14px', cursor: 'pointer', marginBottom: '12px' }}>
              {isLoading ? 'Updating...' : 'Set New Password'}
            </button>
            <div style={{ textAlign: 'center' }}>
              <button 
                type="button"
                onClick={() => setAuthMode('login')} 
                style={{ background: 'none', border: 'none', color: themeSubtext, fontSize: '12px', cursor: 'pointer', fontWeight: '600' }}>
                ← Back to Sign In
              </button>
            </div>
          </form>
        )}

        {/* Demo Fast Logins */}
        <div style={{ marginTop: '24px', paddingTop: '18px', borderTop: `1px solid ${themeBorder}`, textAlign: 'center' }}>
          <span style={{ fontSize: '11px', color: themeSubtext, display: 'block', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '700' }}>
            One-Click Demo Logins
          </span>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
            <button 
              type="button"
              onClick={() => handleQuickDemoLogin('admin@carbonledger.io', 'Admin@12345')} 
              style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #8b5cf6', background: 'rgba(139,92,246,0.12)', color: '#c084fc', cursor: 'pointer', fontSize: '11px', fontWeight: '700' }}>
              👑 Master Admin
            </button>
            <button 
              type="button"
              onClick={() => handleQuickDemoLogin('subscriber@carbonledger.io', 'Subscriber@12345')} 
              style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #10b981', background: 'rgba(16,185,129,0.12)', color: '#34d399', cursor: 'pointer', fontSize: '11px', fontWeight: '700' }}>
              🌿 Paid Subscriber
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
