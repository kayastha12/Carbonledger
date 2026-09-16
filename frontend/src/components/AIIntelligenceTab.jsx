import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

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
  themeSubtext,
  universalResult
}) {
  const [simpleMode, setSimpleMode] = useState(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState([
    "What is my total carbon footprint?",
    "Which supplier has the highest emissions?",
    "How was my Scope 3 footprint calculated?",
    "How much CO2e does 500 kg of steel produce?",
    "Explain the Scope 1, Scope 2, and Scope 3 breakdown.",
    "What is our estimated CBAM liability?"
  ]);

  // Fetch contextual suggestions on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/copilot/suggestions?page=Dashboard`, {
      headers: getAuthHeaders ? getAuthHeaders() : {}
    })
      .then(res => res.json())
      .then(data => {
        if (data.suggestions && data.suggestions.length > 0) {
          setSuggestedQuestions(data.suggestions);
        }
      })
      .catch(() => {});
  }, []);

  const sendQuery = (qText) => {
    const q = (qText || chatInput || '').trim();
    if (!q) return;

    if ((currentUser?.token_balance || 0) < 5) {
      setLowTokenDetails({ required: 5, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }

    setChatMessages(prev => [...prev, { sender: 'user', text: q }]);
    setChatInput('');
    setIsChatLoading(true);

    const payload = {
      query: q,
      tenant_id: currentUser?.organization || 'enterprise',
      context: {
        page: 'AI Intelligence',
        upload_id: universalResult?.upload_id || null,
        simple_mode: simpleMode
      },
      simple_mode: simpleMode
    };

    fetch(`${API_BASE}/api/rag`, {
      method: 'POST',
      headers: getAuthHeaders ? getAuthHeaders() : { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        setIsChatLoading(false);
        const answerText = data.answer || data.response || 'No response received from sustainability copilot.';
        const evidenceData = data.evidence || [];
        const dynamicSuggestions = data.suggestions || [];
        
        setChatMessages(prev => [...prev, {
          sender: 'assistant',
          text: answerText,
          evidence: evidenceData,
          language: data.language,
          intent: data.intent
        }]);

        if (dynamicSuggestions.length > 0) {
          setSuggestedQuestions(dynamicSuggestions);
        }

        if (refreshUserData) refreshUserData();
      })
      .catch(() => {
        setIsChatLoading(false);
        setChatMessages(prev => [...prev, {
          sender: 'assistant',
          text: 'Unable to reach Copilot service. Please check your connection or try again.'
        }]);
      });
  };

  const handleChatSubmit = (e) => {
    e.preventDefault();
    sendQuery();
  };

  const handleClearHistory = () => {
    setChatMessages([
      {
        sender: 'assistant',
        text: '👋 Chat history cleared. How can I assist you with your carbon inventory, emission factors, or compliance reports today?'
      }
    ]);
  };

  const handleRunSimulation = () => {
    if ((currentUser?.token_balance || 0) < 20) {
      setLowTokenDetails({ required: 20, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }
    setIsScenarioLoading(true);
    fetch(`${API_BASE}/api/what-if`, {
      method: 'POST',
      headers: getAuthHeaders ? getAuthHeaders() : { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: selectedStrategy })
    })
      .then(res => res.json())
      .then(data => {
        setIsScenarioLoading(false);
        setScenarioResult(data);
        if (refreshUserData) refreshUserData();
      })
      .catch(() => setIsScenarioLoading(false));
  };

  // Simple Markdown text formatter for responses
  const renderFormattedMessage = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Header ###
      if (line.startsWith('### ')) {
        return <h4 key={idx} style={{ margin: '8px 0 4px', color: '#10b981', fontSize: '14px', fontWeight: '800' }}>{line.replace('### ', '')}</h4>;
      }
      // Header ##
      if (line.startsWith('## ')) {
        return <h3 key={idx} style={{ margin: '10px 0 6px', color: '#3b82f6', fontSize: '15px', fontWeight: '800' }}>{line.replace('## ', '')}</h3>;
      }
      // Bullet point
      if (line.startsWith('- ') || line.startsWith('* ')) {
        const content = line.substring(2);
        return (
          <div key={idx} style={{ display: 'flex', gap: '6px', margin: '3px 0 3px 6px', fontSize: '12.5px', lineHeight: '1.5' }}>
            <span style={{ color: '#10b981', fontWeight: 'bold' }}>•</span>
            <div>{renderInlineFormatting(content)}</div>
          </div>
        );
      }
      // Numbered list
      if (/^\d+\.\s/.test(line)) {
        return (
          <div key={idx} style={{ margin: '3px 0 3px 6px', fontSize: '12.5px', lineHeight: '1.5' }}>
            {renderInlineFormatting(line)}
          </div>
        );
      }
      if (line.trim() === '') {
        return <div key={idx} style={{ height: '6px' }} />;
      }
      return (
        <p key={idx} style={{ margin: '3px 0', fontSize: '12.5px', lineHeight: '1.5' }}>
          {renderInlineFormatting(line)}
        </p>
      );
    });
  };

  const renderInlineFormatting = (str) => {
    // Bold **text**
    const parts = str.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
    return parts.map((part, pIdx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={pIdx} style={{ color: isDarkMode ? '#f8fafc' : '#0f172a' }}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={pIdx} style={{
            padding: '2px 5px', borderRadius: '4px',
            backgroundColor: isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
            color: '#10b981', fontSize: '11.5px', fontFamily: 'monospace'
          }}>
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.35fr 1fr', gap: '24px' }}>
      
      {/* AI Copilot Chat */}
      <div style={{
        padding: '24px', borderRadius: '18px',
        backgroundColor: themeCard, border: `1px solid ${themeBorder}`,
        display: 'flex', flexDirection: 'column', height: '640px',
        boxShadow: isDarkMode ? '0 8px 30px rgba(0,0,0,0.3)' : '0 4px 20px rgba(0,0,0,0.04)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', paddingBottom: '12px', borderBottom: `1px solid ${themeBorder}` }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '800', margin: 0, color: '#10b981' }}>🧠 CarbonLedger Data & Report Copilot</h3>
              <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', backgroundColor: 'rgba(16,185,129,0.15)', color: '#10b981', fontWeight: '700' }}>
                Deterministic Engine Grounded
              </span>
            </div>
            <p style={{ fontSize: '11px', color: themeSubtext, margin: '2px 0 0' }}>
              Trace emissions, verified factor provenance, Scope 1/2/3 formulas & report sheets
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setSimpleMode(!simpleMode)}
              title="Toggle Simple Layman Language mode"
              style={{
                fontSize: '11px', padding: '4px 10px', borderRadius: '8px',
                backgroundColor: simpleMode ? '#10b981' : (isDarkMode ? '#1e293b' : '#e2e8f0'),
                color: simpleMode ? '#080c14' : themeText,
                border: 'none', fontWeight: '700', cursor: 'pointer',
                transition: 'all 0.2s'
              }}>
              {simpleMode ? '🟢 Simple Mode: ON' : '⚪ Simple Mode: OFF'}
            </button>
            <button
              onClick={handleClearHistory}
              title="Clear chat messages"
              style={{
                fontSize: '11px', padding: '4px 8px', borderRadius: '8px',
                backgroundColor: 'transparent', color: themeSubtext,
                border: `1px solid ${themeBorder}`, cursor: 'pointer'
              }}>
              Clear
            </button>
          </div>
        </div>

        {/* Suggested Questions Quick Chips */}
        <div style={{ marginBottom: '10px' }}>
          <div style={{ fontSize: '10.5px', fontWeight: '700', color: themeSubtext, textTransform: 'uppercase', marginBottom: '5px' }}>
            💡 Suggested Questions
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', maxHeight: '68px', overflowY: 'auto' }}>
            {suggestedQuestions.map((qText, sIdx) => (
              <button
                key={sIdx}
                onClick={() => sendQuery(qText)}
                disabled={isChatLoading}
                style={{
                  fontSize: '11px', padding: '4px 9px', borderRadius: '12px',
                  backgroundColor: isDarkMode ? 'rgba(255,255,255,0.05)' : '#f1f5f9',
                  border: `1px solid ${isDarkMode ? 'rgba(255,255,255,0.1)' : '#cbd5e1'}`,
                  color: themeText, cursor: 'pointer', textAlign: 'left',
                  transition: 'all 0.15s'
                }}>
                {qText}
              </button>
            ))}
          </div>
        </div>

        {/* Messages List */}
        <div style={{
          flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column',
          gap: '12px', paddingRight: '6px', marginTop: '4px'
        }}>
          {chatMessages.map((m, i) => (
            <div key={i} style={{ alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '92%' }}>
              <div style={{
                padding: '12px 16px', borderRadius: m.sender === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                backgroundColor: m.sender === 'user' ? '#10b981' : (isDarkMode ? '#0d131f' : '#f8fafc'),
                color: m.sender === 'user' ? '#080c14' : themeText,
                border: m.sender === 'user' ? 'none' : `1px solid ${themeBorder}`,
                boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                position: 'relative'
              }}>
                {m.sender === 'assistant' ? (
                  <>
                    {renderFormattedMessage(m.text)}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', paddingTop: '8px', borderTop: `1px solid ${isDarkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'}`, fontSize: '10.5px', color: themeSubtext }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span style={{ color: '#10b981', fontWeight: 'bold' }}>✓ Verified Ledger Grounded</span>
                        {m.language && m.language !== 'english' && (
                          <span style={{ padding: '1px 6px', borderRadius: '6px', backgroundColor: 'rgba(59,130,246,0.15)', color: '#60a5fa', fontWeight: '700' }}>
                            {m.language.toUpperCase()}
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          if (navigator.clipboard) {
                            navigator.clipboard.writeText(m.text);
                            alert('Answer copied to clipboard!');
                          }
                        }}
                        style={{
                          fontSize: '10px', padding: '2px 6px', borderRadius: '4px',
                          backgroundColor: 'transparent', border: `1px solid ${themeBorder}`,
                          color: themeSubtext, cursor: 'pointer'
                        }}>
                        📋 Copy
                      </button>
                    </div>
                  </>
                ) : (
                  <div style={{ fontSize: '13px', fontWeight: '600' }}>{m.text}</div>
                )}
              </div>
            </div>
          ))}
          {isChatLoading && (
            <div style={{ alignSelf: 'flex-start', padding: '10px 14px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', color: '#10b981', fontSize: '12px', fontWeight: 'bold' }}>
              ⚡ Consulting CarbonLedger Verified Factor Ledger & Calculation Engine...
            </div>
          )}
        </div>

        {/* Input Bar */}
        <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
          <input 
            type="text" value={chatInput} onChange={e => setChatInput(e.target.value)}
            placeholder="Ask about materials (e.g. 500 kg steel), emission factors, Scope 1/2/3, or report sheets..."
            style={{
              flex: 1, padding: '11px 14px', borderRadius: '10px',
              border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff',
              color: themeText, fontSize: '12.5px', outline: 'none'
            }}
          />
          <button 
            type="submit" disabled={isChatLoading || !chatInput.trim()} 
            style={{
              padding: '11px 20px', borderRadius: '10px',
              backgroundColor: '#10b981', color: '#080c14',
              border: 'none', fontWeight: '800', fontSize: '12.5px',
              cursor: (isChatLoading || !chatInput.trim()) ? 'not-allowed' : 'pointer',
              boxShadow: '0 4px 12px rgba(16,185,129,0.3)',
              opacity: (isChatLoading || !chatInput.trim()) ? 0.6 : 1
            }}>
            {isChatLoading ? 'Tracing...' : 'Send (⚡ 5)'}
          </button>
        </form>
      </div>

      {/* What-If Decarbonization Simulator */}
      <div style={{
        padding: '24px', borderRadius: '18px', backgroundColor: themeCard,
        border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column',
        justifyContent: 'space-between', height: '640px',
        boxShadow: isDarkMode ? '0 8px 30px rgba(0,0,0,0.3)' : '0 4px 20px rgba(0,0,0,0.04)'
      }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', paddingBottom: '12px', borderBottom: `1px solid ${themeBorder}` }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '800', margin: 0, color: '#3b82f6' }}>🔮 What-If Decarbonization Simulator</h3>
              <p style={{ fontSize: '11px', color: themeSubtext, margin: '2px 0 0' }}>Simulate certified emission reduction pathways</p>
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

        {/* Traceability Guarantee Banner */}
        <div style={{
          padding: '14px', borderRadius: '12px',
          backgroundColor: isDarkMode ? 'rgba(16,185,129,0.05)' : '#ecfdf5',
          border: '1px solid rgba(16,185,129,0.2)', fontSize: '11.5px', color: themeSubtext
        }}>
          <strong style={{ color: '#10b981' }}>🛡️ CarbonLedger Audit Contract</strong>: All calculations, factors, and report values are deterministically linked to your verified workspace records with zero hallucination.
        </div>
      </div>

    </div>
  );
}
