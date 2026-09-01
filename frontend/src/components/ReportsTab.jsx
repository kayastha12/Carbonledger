import React from 'react';

export default function ReportsTab({
  universalResult,
  currentUser,
  currentSub,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  const reportCards = [
    { name: 'Official CBAM Declaration (Excel)', key: 'cbam_report_excel', icon: '📊', type: 'Official CBAM XML / XLSX Format', desc: 'Direct embedded emissions and CBAM certificates exposure for customs filing.' },
    { name: 'Corporate Carbon Inventory (Excel)', key: 'inventory_excel', icon: '📑', type: 'GHG Protocol Worksheets', desc: 'Complete multi-facility Scope 1, Scope 2, and Scope 3 breakdown.' },
    { name: 'Executive ESG Compliance Report (PDF)', key: 'executive_esg_pdf', icon: '📄', type: 'Boardroom Summary PDF', desc: 'High-level decarbonization trajectory, benchmarks, and audit pass rates.' },
    { name: 'Cryptographic Audit Trail (JSON)', key: 'audit_json', icon: '📜', type: 'SHA-256 Verified Ledger', desc: 'Immutable trace logs for ISO 14064 compliance verification.' }
  ];

  return (
    <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 6px 0', color: '#10b981' }}>
            📑 Enterprise Compliance & ESG Reports
          </h3>
          <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>
            Download verified carbon inventory workbooks and regulatory declarations.
          </p>
        </div>
        <span style={{ fontSize: '11px', padding: '6px 12px', borderRadius: '20px', backgroundColor: 'rgba(59,130,246,0.1)', color: '#60a5fa', fontWeight: '800' }}>
          Included with {currentSub?.plan_tier?.toUpperCase()} Plan
        </span>
      </div>

      {universalResult && universalResult.reports ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
          {reportCards.map((rep, idx) => (
            <div key={idx} style={{ padding: '24px', borderRadius: '14px', backgroundColor: isDarkMode ? '#080c14' : '#f8fafc', border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '28px', marginBottom: '10px' }}>{rep.icon}</div>
                <h4 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 4px 0', color: themeText }}>{rep.name}</h4>
                <div style={{ fontSize: '11px', color: '#10b981', fontWeight: 'bold', marginBottom: '8px' }}>{rep.type}</div>
                <p style={{ fontSize: '12px', color: themeSubtext, margin: '0 0 20px 0', lineHeight: 1.4 }}>{rep.desc}</p>
              </div>
              <a 
                href={universalResult.reports[rep.key]}
                target="_blank" rel="noreferrer"
                style={{
                  padding: '10px 16px', borderRadius: '8px', backgroundColor: '#10b981', color: '#080c14',
                  textDecoration: 'none', fontWeight: '800', fontSize: '13px', textAlign: 'center',
                  boxShadow: '0 4px 12px rgba(16,185,129,0.3)'
                }}>
                Download Report
              </a>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '48px 20px', color: themeSubtext, fontSize: '13px' }}>
          <div style={{ fontSize: '36px', marginBottom: '10px' }}>📑</div>
          <div style={{ fontWeight: 'bold', color: themeText, marginBottom: '4px' }}>No Reports Generated in Current Session</div>
          Upload and calculate an invoice or carbon dataset to automatically generate official compliance exports.
        </div>
      )}
    </div>
  );
}

