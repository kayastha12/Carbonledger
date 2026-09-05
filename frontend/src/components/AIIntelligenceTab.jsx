import React from 'react';

export default function AIIntelligenceTab({
  currentUser,
  chatMessages,
  setChatMessages,
  chatInput,
  setChatInput,
  isChatLoading,
  setIsChatLoading,
  selectedStrategy,
  setSelectedStrategy,
  scenarioResult,
  setScenarioResult,
  isScenarioLoading,
  setIsScenarioLoading,
  setLowTokenDetails,
  setShowLowTokenModal,
  refreshUserData,
  getAuthHeaders,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  const handleChatSubmit = (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    if ((currentUser?.token_balance || 0) < 5) {
      setLowTokenDetails({ required: 5, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }
    const q = chatInput;
    setChatMessages(prev => [...prev, { sender: 'user', text: q }]);
    setChatInput('');
    setIsChatLoading(true);

    fetch('http://localhost:8000/api/rag', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query: q, tenant_id: currentUser?.organization || 'enterprise' })
    })
    .then(res => res.json())
    .then(data => {
      setIsChatLoading(false);
      const answerText = data.answer || data.response || 'No response received from sustainability assistant.';
      setChatMessages(prev => [...prev, { sender: 'assistant', text: answerText }]);
      refreshUserData();
    })
    .catch(() => {
      setIsChatLoading(false);
      setChatMessages(prev => [...prev, { sender: 'assistant', text: 'Unable to reach assistant service. Please check your network connection.' }]);
    });
  };

  const handleRunSimulation = () => {
    if ((currentUser?.token_balance || 0) < 20) {
      setLowTokenDetails({ required: 20, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }
    setIsScenarioLoading(true);
    fetch('http://localhost:8000/api/what-if', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ strategy: selectedStrategy })
    })
    .then(res => res.json())
    .then(data => {
      setIsScenarioLoading(false);
      setScenarioResult(data);
      refreshUserData();
    })
    .catch(() => setIsScenarioLoading(false));
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
      
      {/* AI Copilot Chat */}
      <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column', height: '560px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h3 style={{ fontSize: '17px', fontWeight: '800', margin: 0, color: '#10b981' }}>🧠 AI Sustainability Copilot</h3>
            <p style={{ fontSize: '11px', color: themeSubtext, margin: '2px 0 0' }}>Ask questions about your emissions and CBAM certificates</p>
          </div>
          <span style={{ fontSize: '10px', padding: '4px 10px', borderRadius: '12px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', fontWeight: 'bold' }}>
            ⚡ 5 Tokens / query
          </span>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '6px' }}>
          {chatMessages.map((m, i) => (
            <div key={i} style={{ alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
              <div style={{
                padding: '10px 14px', borderRadius: '12px',
                backgroundColor: m.sender === 'user' ? '#10b981' : (isDarkMode ? '#080c14' : '#f1f5f9'),
                color: m.sender === 'user' ? '#080c14' : themeText,
                fontSize: '13px', fontWeight: m.sender === 'user' ? '600' : 'normal',
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
              }}>
                {m.text}
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '8px', marginTop: '14px' }}>
          <input 
            type="text" value={chatInput} onChange={e => setChatInput(e.target.value)}
            placeholder="Ask a question (e.g. Which supplier has highest emissions?)..."
            style={{ flex: 1, padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '12px', outline: 'none' }}
          />
          <button 
            type="submit" disabled={isChatLoading} 
            style={{ padding: '10px 18px', borderRadius: '8px', backgroundColor: '#10b981', color: '#080c14', border: 'none', fontWeight: '800', fontSize: '12px', cursor: 'pointer', boxShadow: '0 4px 12px rgba(16,185,129,0.3)' }}>
            {isChatLoading ? 'Thinking...' : 'Send (⚡ 5)'}
          </button>
        </form>
      </div>

      {/* What-If Decarbonization Simulator */}
      <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div>
              <h3 style={{ fontSize: '17px', fontWeight: '800', margin: 0, color: '#3b82f6' }}>🔮 What-If Decarbonization Simulator</h3>
              <p style={{ fontSize: '11px', color: themeSubtext, margin: '2px 0 0' }}>Simulate emission reduction pathways</p>
            </div>
            <span style={{ fontSize: '10px', padding: '4px 10px', borderRadius: '12px', backgroundColor: 'rgba(59,130,246,0.1)', color: '#60a5fa', fontWeight: 'bold' }}>
              ⚡ 20 Tokens
            </span>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px', color: themeText }}>Decarbonization Pathway</label>
            <select 
              value={selectedStrategy} onChange={e => setSelectedStrategy(e.target.value)}
              style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '12px' }}>
              <option value="eaf_steel">Switch to Electric Arc Furnace (EAF) Steel (-65% CO₂e)</option>
              <option value="renewable_grid">100% PPA Renewable Electricity Grid (-85% Scope 2)</option>
              <option value="supplier_nearshoring">Nearshore Value Chain Logistics (-40% Freight)</option>
            </select>
          </div>

          <button 
            onClick={handleRunSimulation}
            disabled={isScenarioLoading}
            style={{ width: '100%', padding: '11px', borderRadius: '8px', backgroundColor: '#3b82f6', color: '#fff', border: 'none', fontWeight: '800', fontSize: '13px', cursor: 'pointer', marginBottom: '16px', boxShadow: '0 4px 12px rgba(59,130,246,0.3)' }}>
            {isScenarioLoading ? 'Simulating Pathway...' : 'Run Simulation (⚡ 20 Tokens)'}
          </button>

          {scenarioResult && (
            <div style={{ padding: '18px', borderRadius: '12px', backgroundColor: isDarkMode ? '#080c14' : '#f1f5f9', border: `1px solid ${themeBorder}` }}>
              <div style={{ fontSize: '12px', color: '#10b981', fontWeight: '800', marginBottom: '8px', textTransform: 'uppercase' }}>Simulation Forecast Results:</div>
              <div style={{ fontSize: '13px', color: themeText, marginBottom: '4px' }}>Baseline Footprint: <strong>{scenarioResult.baseline_emissions_t} tonnes CO₂e</strong></div>
              <div style={{ fontSize: '13px', color: '#10b981', marginBottom: '4px' }}>Projected Footprint: <strong>{scenarioResult.projected_emissions_t} tonnes (-{scenarioResult.reduction_pct}%)</strong></div>
              <div style={{ fontSize: '12px', color: themeSubtext, marginTop: '6px' }}>Estimated CBAM Cost Savings: <strong>€{scenarioResult.estimated_cbam_savings_eur}</strong></div>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

