import React from 'react';

export default function DashboardTab({
  currentUser,
  currentSub,
  universalResult,
  userActivities,
  carbonPrice,
  setActiveTab,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  const hasUpload = Boolean(universalResult && universalResult.records && universalResult.records.length > 0);
  const summary = universalResult?.summary || {};

  const docsProcessed = hasUpload ? (summary.documents_processed ?? 1) : 0;
  const lineItemsExtracted = hasUpload ? (summary.rows_extracted ?? universalResult.records.length) : 0;
  const totalCo2eKg = hasUpload ? (summary.total_co2e_kg ?? 0) : 0;
  const totalCo2eTonnes = hasUpload ? (summary.total_co2e_tonnes ?? (totalCo2eKg / 1000.0)) : 0;
  const totalCbamCost = hasUpload ? (summary.total_cbam_cost_eur ?? 0) : 0;

  const hasConfidence = hasUpload && universalResult.ai_confidence != null && universalResult.ai_confidence > 0;
  const aiConfidenceVal = hasConfidence ? `${Number(universalResult.ai_confidence).toFixed(1)}%` : '—';
  const aiConfidenceSub = hasConfidence ? 'Live OCR Confidence' : 'No active scan';

  const rowsCalculated = summary.rows_calculated ?? 0;
  let calcStatus = 'NO DATA';
  let calcStatusSub = 'Awaiting document';
  let calcStatusColor = '#64748b';

  if (hasUpload) {
    if (universalResult.status === 'parsed' || rowsCalculated === 0) {
      calcStatus = 'PENDING';
      calcStatusSub = 'Awaiting Review Approval';
      calcStatusColor = '#f59e0b';
    } else {
      calcStatus = 'AUDITED';
      calcStatusSub = `${rowsCalculated} of ${lineItemsExtracted} Factors Matched`;
      calcStatusColor = '#10b981';
    }
  }

  const scope1Kg = hasUpload ? (summary.scope_1_co2e_kg ?? 0) : 0;
  const scope2Kg = hasUpload ? (summary.scope_2_co2e_kg ?? 0) : 0;
  const scope3Kg = hasUpload ? (summary.scope_3_co2e_kg ?? 0) : 0;

  const kpis = [
    {
      label: 'Documents Processed',
      val: docsProcessed,
      sub: hasUpload ? 'In Current Session' : 'No uploads yet',
      icon: '📄',
      color: '#3b82f6'
    },
    {
      label: 'Extracted Line Items',
      val: lineItemsExtracted,
      sub: hasUpload ? 'Real Extracted Rows' : '0 records',
      icon: '📊',
      color: '#10b981'
    },
    {
      label: 'Total Footprint',
      val: `${totalCo2eKg.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} kg`,
      sub: `${totalCo2eTonnes.toFixed(3)} tonnes CO₂e`,
      icon: '🌍',
      color: '#f59e0b'
    },
    {
      label: 'CBAM Cost Exposure',
      val: `€${totalCbamCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      sub: `@ €${carbonPrice}/t benchmark`,
      icon: '💶',
      color: '#8b5cf6'
    },
    {
      label: 'AI OCR Confidence',
      val: aiConfidenceVal,
      sub: aiConfidenceSub,
      icon: '🛡️',
      color: '#06b6d4'
    },
    {
      label: 'Calculation Status',
      val: calcStatus,
      sub: calcStatusSub,
      icon: calcStatus === 'AUDITED' ? '✅' : (calcStatus === 'PENDING' ? '⏳' : '⚪'),
      color: calcStatusColor
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* Welcome Banner */}
      <div style={{
        padding: '24px', borderRadius: '18px',
        background: 'linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(59,130,246,0.05) 100%)',
        border: `1px solid ${themeBorder}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 6px 0', color: themeText }}>
            Welcome to {currentUser?.organization || 'Your Workspace'} 👋
          </h3>
          <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>
            Active Subscription: <strong>{currentSub?.plan_tier?.toUpperCase() || 'TRIAL'}</strong> • Region: <strong>{currentUser?.default_region || 'DE'}</strong> • Role: <strong>{currentUser?.role?.toUpperCase() || 'USER'}</strong>
          </p>
        </div>
        <button 
          onClick={() => setActiveTab('Upload & Review')}
          style={{ padding: '10px 20px', borderRadius: '10px', backgroundColor: '#10b981', color: '#080c14', border: 'none', fontWeight: '800', fontSize: '13px', cursor: 'pointer', boxShadow: '0 4px 12px rgba(16,185,129,0.3)' }}>
          + Upload Document
        </button>
      </div>

      {/* 6 Real-time KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        {kpis.map((kpi, idx) => (
          <div key={idx} style={{ padding: '20px', borderRadius: '16px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: '700', color: themeSubtext, textTransform: 'uppercase' }}>{kpi.label}</span>
              <span style={{ fontSize: '16px' }}>{kpi.icon}</span>
            </div>
            <div style={{ fontSize: '20px', fontWeight: '800', color: kpi.color, marginBottom: '4px' }}>{kpi.val}</div>
            <div style={{ fontSize: '11px', color: themeSubtext }}>{kpi.sub}</div>
          </div>
        ))}
      </div>

      {/* Scope Distribution Bar */}
      <div style={{ padding: '24px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
        <h4 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 16px 0', color: themeText }}>🌿 GHG Scope Breakdown</h4>
        <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
          <div style={{ flex: 1, padding: '14px', borderRadius: '10px', backgroundColor: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)' }}>
            <div style={{ fontSize: '11px', color: themeSubtext, fontWeight: '600' }}>Scope 1 (Direct Fuels)</div>
            <div style={{ fontSize: '18px', fontWeight: '800', color: '#10b981', marginTop: '4px' }}>{scope1Kg.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} kg</div>
          </div>
          <div style={{ flex: 1, padding: '14px', borderRadius: '10px', backgroundColor: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)' }}>
            <div style={{ fontSize: '11px', color: themeSubtext, fontWeight: '600' }}>Scope 2 (Electricity Grid)</div>
            <div style={{ fontSize: '18px', fontWeight: '800', color: '#3b82f6', marginTop: '4px' }}>{scope2Kg.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} kg</div>
          </div>
          <div style={{ flex: 1, padding: '14px', borderRadius: '10px', backgroundColor: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)' }}>
            <div style={{ fontSize: '11px', color: themeSubtext, fontWeight: '600' }}>Scope 3 (Value Chain / CBAM)</div>
            <div style={{ fontSize: '18px', fontWeight: '800', color: '#f59e0b', marginTop: '4px' }}>{scope3Kg.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} kg</div>
          </div>
        </div>
      </div>

      {/* No Document Callout if zero uploads */}
      {!hasUpload && (
        <div style={{
          backgroundColor: themeCard, border: `1px dashed ${themeBorder}`, borderRadius: '18px',
          padding: '32px 24px', textAlign: 'center'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '12px' }}>📂</div>
          <h4 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 6px 0', color: themeText }}>
            No Carbon Documents Uploaded in Current Session
          </h4>
          <p style={{ fontSize: '13px', color: themeSubtext, maxWidth: '460px', margin: '0 auto 16px auto', lineHeight: 1.5 }}>
            Upload utility invoices, purchase orders, or shipping manifests to compute live carbon footprints and CBAM exposure.
          </p>
          <button 
            onClick={() => setActiveTab('Upload & Review')}
            style={{ padding: '10px 20px', borderRadius: '10px', backgroundColor: '#3b82f6', color: '#ffffff', border: 'none', fontWeight: '800', fontSize: '13px', cursor: 'pointer', boxShadow: '0 4px 12px rgba(59,130,246,0.3)' }}>
            Start Document Extraction (⚡ 15 Tokens)
          </button>
        </div>
      )}

      {/* Recent Activity Log */}
      <div style={{ padding: '24px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
        <h4 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 16px 0', color: themeText }}>📜 Recent Activity & Audit Timeline</h4>
        {!userActivities || userActivities.length === 0 ? (
          <div style={{ fontSize: '12px', color: themeSubtext, textAlign: 'center', padding: '20px' }}>No activity yet</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {userActivities.slice(0, 6).map((act, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', borderRadius: '8px', backgroundColor: isDarkMode ? '#080c14' : '#f8fafc', border: `1px solid ${themeBorder}`, fontSize: '12px' }}>
                <div>
                  <span style={{ fontWeight: 'bold', color: '#10b981', marginRight: '8px' }}>● {act.activity_type}</span>
                  <span style={{ color: themeText }}>{act.description}</span>
                </div>
                <span style={{ color: themeSubtext, fontSize: '11px' }}>{act.created_at}</span>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}


