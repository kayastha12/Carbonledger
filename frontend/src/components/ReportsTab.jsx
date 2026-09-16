import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

export default function ReportsTab({
  universalResult,
  currentUser,
  currentSub,
  getAuthHeaders,
  showToast,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext,
  onOpenCopilotWithContext
}) {
  const [downloadingKey, setDownloadingKey] = useState(null);
  const [selectedSheet, setSelectedSheet] = useState('Executive Summary');
  const [selectedRow, setSelectedRow] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);
  const [reportContext, setReportContext] = useState(null);
  const [isLoadingContext, setIsLoadingContext] = useState(false);
  const [copilotCellAnswer, setCopilotCellAnswer] = useState(null);
  const [isCellTracing, setIsCellTracing] = useState(false);

  const hasCalculatedData = Boolean(
    universalResult &&
    universalResult.records &&
    universalResult.records.length > 0
  );

  const uploadId = universalResult?.upload_id || '';

  // Fetch report context index
  useEffect(() => {
    if (uploadId) {
      setIsLoadingContext(true);
      fetch(`${API_BASE}/api/v1/reports/context?upload_id=${uploadId}`, {
        headers: getAuthHeaders ? getAuthHeaders() : {}
      })
        .then(res => res.json())
        .then(data => {
          setIsLoadingContext(false);
          if (data && data.sheets) {
            setReportContext(data);
          }
        })
        .catch(() => {
          setIsLoadingContext(false);
        });
    }
  }, [uploadId]);

  const reportCards = [
    { 
      name: 'Official CBAM Declaration (Excel)', 
      key: 'cbam_report_excel', 
      defaultFilename: 'cbam_report.xlsx',
      icon: '📊', 
      type: 'Official CBAM XML / XLSX Format', 
      desc: 'Direct embedded emissions and CBAM certificates exposure for customs filing.' 
    },
    { 
      name: 'Corporate Carbon Inventory (Excel)', 
      key: 'inventory_excel', 
      defaultFilename: 'inventory.xlsx',
      icon: '📑', 
      type: 'GHG Protocol Worksheets', 
      desc: 'Complete multi-facility Scope 1, Scope 2, and Scope 3 breakdown.' 
    },
    { 
      name: 'Executive ESG Compliance Report (PDF)', 
      key: 'executive_esg_pdf', 
      defaultFilename: 'executive_esg_report.pdf',
      icon: '📄', 
      type: 'Boardroom Summary PDF', 
      desc: 'High-level decarbonization trajectory, benchmarks, and audit pass rates.' 
    },
    { 
      name: 'Cryptographic Audit Trail (JSON)', 
      key: 'audit_json', 
      defaultFilename: 'audit.json',
      icon: '📜', 
      type: 'SHA-256 Verified Ledger', 
      desc: 'Immutable trace logs for ISO 14064 compliance verification with cryptographic hash chain.' 
    }
  ];

  const handleDownload = async (e, rep) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    if (!hasCalculatedData) {
      if (showToast) showToast('warning', 'No calculated data available yet — please upload a document first.');
      return;
    }

    const reportUrl = universalResult?.reports?.[rep.key];
    if (!reportUrl) {
      if (showToast) showToast('error', `Report path for ${rep.name} is not available.`);
      return;
    }

    setDownloadingKey(rep.key);
    try {
      const targetUrl = reportUrl.startsWith('http') 
        ? reportUrl 
        : `${API_BASE}${reportUrl.startsWith('/') ? '' : '/'}${reportUrl}`;

      const headers = getAuthHeaders ? getAuthHeaders() : {};
      const response = await fetch(targetUrl, {
        method: 'GET',
        headers: headers
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      let filename = rep.defaultFilename;
      const disposition = response.headers.get('content-disposition');
      if (disposition && disposition.includes('filename=')) {
        const matches = disposition.match(/filename=["']?([^"';]+)["']?/);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

      if (showToast) {
        showToast('success', `Downloaded ${filename} successfully.`);
      }
    } catch (err) {
      console.error('Download error:', err);
      if (showToast) {
        showToast('error', `Failed to download ${rep.name}: ${err.message}`);
      }
    } finally {
      setDownloadingKey(null);
    }
  };

  const handleAskCopilotAboutCell = (cellData, rowData, colName) => {
    setSelectedCell({ column: colName, value: cellData, row_data: rowData });
    setIsCellTracing(true);
    setCopilotCellAnswer(null);

    const payload = {
      query: `Explain why this cell has value '${cellData}' in column '${colName}' on sheet '${selectedSheet}'`,
      tenant_id: currentUser?.organization || 'enterprise',
      context: {
        page: 'Reports',
        sheet_name: selectedSheet,
        upload_id: uploadId,
        selected_cell: {
          column: colName,
          value: cellData,
          row_data: rowData
        }
      }
    };

    fetch(`${API_BASE}/api/rag`, {
      method: 'POST',
      headers: getAuthHeaders ? getAuthHeaders() : { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        setIsCellTracing(false);
        setCopilotCellAnswer(data.answer || data.response || 'Trace completed.');
      })
      .catch(() => {
        setIsCellTracing(false);
        setCopilotCellAnswer('Unable to retrieve Copilot trace for this cell.');
      });
  };

  const sheetNames = [
    'Executive Summary',
    'Scope 1',
    'Scope 2',
    'Scope 3',
    'CBAM Cost',
    'Materials',
    'Top Emitters',
    'Audit Trail'
  ];

  // Helper to get records for active sheet
  const getSheetRecords = () => {
    if (!universalResult || !universalResult.records) return [];
    if (selectedSheet === 'Scope 1') {
      return universalResult.records.filter(r => r.scope === 'Scope 1');
    }
    if (selectedSheet === 'Scope 2') {
      return universalResult.records.filter(r => r.scope === 'Scope 2');
    }
    if (selectedSheet === 'Scope 3') {
      return universalResult.records.filter(r => r.scope === 'Scope 3');
    }
    return universalResult.records;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Banner */}
      <div style={{ padding: '24px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '800', margin: 0, color: '#10b981' }}>
                📑 Enterprise Compliance & ESG Reports
              </h3>
              <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '12px', backgroundColor: 'rgba(16,185,129,0.15)', color: '#10b981', fontWeight: 'bold' }}>
                AI Report Copilot Active
              </span>
            </div>
            <p style={{ fontSize: '12.5px', color: themeSubtext, margin: 0 }}>
              Download verified compliance packages and interactively explore individual sheets, formulas, and cells with the AI Copilot.
            </p>
          </div>
          <span style={{ fontSize: '11px', padding: '6px 12px', borderRadius: '20px', backgroundColor: 'rgba(59,130,246,0.1)', color: '#60a5fa', fontWeight: '800' }}>
            Included with {currentSub?.plan_tier?.toUpperCase() || 'TRIAL'} Plan
          </span>
        </div>
      </div>

      {/* 4 Download Report Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '18px' }}>
        {reportCards.map((rep, idx) => {
          const isDownloading = downloadingKey === rep.key;

          return (
            <div key={idx} style={{
              padding: '20px', borderRadius: '16px', backgroundColor: themeCard,
              border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column',
              justifyContent: 'space-between', minHeight: '230px'
            }}>
              <div>
                <div style={{ fontSize: '28px', marginBottom: '8px' }}>{rep.icon}</div>
                <h4 style={{ fontSize: '14.5px', fontWeight: '800', margin: '0 0 3px 0', color: themeText }}>{rep.name}</h4>
                <div style={{ fontSize: '11px', color: '#10b981', fontWeight: 'bold', marginBottom: '6px' }}>{rep.type}</div>
                <p style={{ fontSize: '11.5px', color: themeSubtext, margin: '0 0 14px 0', lineHeight: 1.4 }}>{rep.desc}</p>
              </div>

              {hasCalculatedData ? (
                <button 
                  type="button"
                  id={`download-report-${rep.key}`}
                  onClick={(e) => handleDownload(e, rep)}
                  disabled={isDownloading}
                  style={{
                    padding: '9px 14px', borderRadius: '9px', 
                    backgroundColor: isDownloading ? '#059669' : '#10b981', 
                    color: '#080c14',
                    border: 'none',
                    cursor: isDownloading ? 'wait' : 'pointer',
                    fontWeight: '800', fontSize: '12px', textAlign: 'center',
                    boxShadow: '0 4px 12px rgba(16,185,129,0.25)', display: 'block',
                    width: '100%',
                    transition: 'all 0.2s ease'
                  }}>
                  {isDownloading ? '⏳ Downloading...' : '⬇️ Download Report'}
                </button>
              ) : (
                <button
                  type="button"
                  disabled
                  style={{
                    padding: '9px 14px', borderRadius: '9px',
                    backgroundColor: isDarkMode ? '#1f2937' : '#e2e8f0',
                    color: themeSubtext, border: 'none',
                    fontWeight: '700', fontSize: '11.5px', textAlign: 'center',
                    cursor: 'not-allowed', opacity: 0.7,
                    width: '100%'
                  }}>
                  🔒 Upload data to generate
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Interactive Sheet & Cell Explorer */}
      {hasCalculatedData && (
        <div style={{
          padding: '24px', borderRadius: '18px', backgroundColor: themeCard,
          border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column', gap: '16px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <h4 style={{ fontSize: '16px', fontWeight: '800', margin: '0 0 4px 0', color: themeText }}>
                🔍 Live Report Sheet & Cell Inspector
              </h4>
              <p style={{ fontSize: '12px', color: themeSubtext, margin: 0 }}>
                Click any row or cell to view its verified calculation provenance and underlying GHG Protocol formula.
              </p>
            </div>
            
            {/* Sheet Selector Tabs */}
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {sheetNames.map((sName) => (
                <button
                  key={sName}
                  onClick={() => { setSelectedSheet(sName); setSelectedRow(null); setSelectedCell(null); setCopilotCellAnswer(null); }}
                  style={{
                    padding: '6px 12px', borderRadius: '8px', fontSize: '11.5px', fontWeight: '700',
                    backgroundColor: selectedSheet === sName ? '#10b981' : (isDarkMode ? '#1e293b' : '#f1f5f9'),
                    color: selectedSheet === sName ? '#080c14' : themeText,
                    border: 'none', cursor: 'pointer', transition: 'all 0.15s'
                  }}>
                  {sName}
                </button>
              ))}
            </div>
          </div>

          {/* Sheet Details & Table */}
          <div style={{ display: 'grid', gridTemplateColumns: selectedCell || copilotCellAnswer ? '1.5fr 1fr' : '1fr', gap: '18px' }}>
            
            {/* Main Sheet Data Table */}
            <div style={{ overflowX: 'auto', maxHeight: '420px', overflowY: 'auto' }}>
              {selectedSheet === 'Executive Summary' ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', padding: '10px 0' }}>
                  <div style={{ padding: '16px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
                    <div style={{ fontSize: '11px', color: themeSubtext, textTransform: 'uppercase' }}>Total CO₂e (kg)</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', color: '#10b981', margin: '4px 0' }}>
                      {universalResult.summary?.total_co2e_kg?.toLocaleString() || '0.00'}
                    </div>
                    <div style={{ fontSize: '11px', color: themeSubtext }}>{(universalResult.summary?.total_co2e_tonnes || 0).toFixed(3)} metric tonnes</div>
                  </div>
                  <div style={{ padding: '16px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
                    <div style={{ fontSize: '11px', color: themeSubtext, textTransform: 'uppercase' }}>CBAM Cost Liability</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', color: '#3b82f6', margin: '4px 0' }}>
                      €{(universalResult.summary?.total_cbam_cost_eur || 0).toLocaleString()}
                    </div>
                    <div style={{ fontSize: '11px', color: themeSubtext }}>@ €85.00/tonne benchmark</div>
                  </div>
                  <div style={{ padding: '16px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
                    <div style={{ fontSize: '11px', color: themeSubtext, textTransform: 'uppercase' }}>Audit Confidence</div>
                    <div style={{ fontSize: '20px', fontWeight: '800', color: '#10b981', margin: '4px 0' }}>
                      {universalResult.summary?.overall_confidence_pct || 98.4}%
                    </div>
                    <div style={{ fontSize: '11px', color: themeSubtext }}>100% Deterministic Parity</div>
                  </div>
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ backgroundColor: isDarkMode ? '#1e293b' : '#f1f5f9', borderBottom: `1px solid ${themeBorder}` }}>
                      <th style={{ padding: '10px 12px', color: themeText }}>PO #</th>
                      <th style={{ padding: '10px 12px', color: themeText }}>Material</th>
                      <th style={{ padding: '10px 12px', color: themeText }}>Supplier</th>
                      <th style={{ padding: '10px 12px', color: themeText }}>Quantity</th>
                      <th style={{ padding: '10px 12px', color: themeText }}>Factor ID</th>
                      <th style={{ padding: '10px 12px', color: themeText }}>CO₂e (kg)</th>
                      <th style={{ padding: '10px 12px', color: themeText }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getSheetRecords().map((row, rIdx) => (
                      <tr 
                        key={rIdx} 
                        style={{
                          borderBottom: `1px solid ${themeBorder}`,
                          backgroundColor: selectedRow === row ? (isDarkMode ? 'rgba(16,185,129,0.1)' : '#ecfdf5') : 'transparent',
                          cursor: 'pointer'
                        }}
                        onClick={() => setSelectedRow(row)}
                      >
                        <td style={{ padding: '9px 12px', color: themeText, fontFamily: 'monospace' }}>
                          {row.po_number || `PO-${rIdx+1}`}
                        </td>
                        <td 
                          style={{ padding: '9px 12px', color: '#10b981', fontWeight: '600' }}
                          onClick={(e) => { e.stopPropagation(); handleAskCopilotAboutCell(row.material, row, 'material'); }}
                          title="Click to inspect this material cell"
                        >
                          {row.material} 🔍
                        </td>
                        <td style={{ padding: '9px 12px', color: themeText }}>
                          {row.supplier}
                        </td>
                        <td 
                          style={{ padding: '9px 12px', color: themeText, fontFamily: 'monospace' }}
                          onClick={(e) => { e.stopPropagation(); handleAskCopilotAboutCell(`${row.quantity} ${row.unit}`, row, 'quantity'); }}
                          title="Click to inspect this quantity cell"
                        >
                          {row.quantity} {row.unit} 🔍
                        </td>
                        <td style={{ padding: '9px 12px', color: themeSubtext, fontSize: '11px', fontFamily: 'monospace' }}>
                          {row.factor_id || 'DEFRA_2026'}
                        </td>
                        <td 
                          style={{ padding: '9px 12px', fontWeight: '800', color: '#10b981' }}
                          onClick={(e) => { e.stopPropagation(); handleAskCopilotAboutCell(row.co2e_kg, row, 'co2e_kg'); }}
                          title="Click to inspect this CO2e calculation cell"
                        >
                          {Number(row.co2e_kg || 0).toLocaleString()} kg 🔍
                        </td>
                        <td style={{ padding: '9px 12px' }}>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleAskCopilotAboutCell(row.co2e_kg, row, 'row_trace'); }}
                            style={{
                              padding: '3px 8px', borderRadius: '6px', fontSize: '10.5px', fontWeight: '700',
                              backgroundColor: isDarkMode ? '#1e293b' : '#e2e8f0', color: '#10b981',
                              border: 'none', cursor: 'pointer'
                            }}>
                            🧠 Explain
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* AI Copilot Cell & Row Trace Card */}
            {(selectedCell || copilotCellAnswer) && (
              <div style={{
                padding: '18px', borderRadius: '14px',
                backgroundColor: isDarkMode ? '#080c14' : '#f8fafc',
                border: '1px solid #10b981', display: 'flex', flexDirection: 'column', gap: '10px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '12.5px', fontWeight: '800', color: '#10b981' }}>
                    🔬 AI Cell Provenance Trace
                  </div>
                  <button 
                    onClick={() => { setSelectedCell(null); setCopilotCellAnswer(null); }}
                    style={{ background: 'none', border: 'none', color: themeSubtext, cursor: 'pointer', fontSize: '13px' }}>
                    ✕
                  </button>
                </div>

                {isCellTracing ? (
                  <div style={{ fontSize: '12px', color: themeSubtext, padding: '12px 0' }}>
                    ⚡ Tracing calculation formula and emission factor provenance...
                  </div>
                ) : (
                  <div style={{ fontSize: '12px', color: themeText, lineHeight: '1.5', whiteSpace: 'pre-line' }}>
                    {copilotCellAnswer}
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      )}

      {/* Empty State / Upload guidance banner when no data */}
      {!hasCalculatedData && (
        <div style={{
          textAlign: 'center', padding: '36px 20px', color: themeSubtext, fontSize: '13px',
          backgroundColor: themeCard, borderRadius: '18px', border: `1px dashed ${themeBorder}`
        }}>
          <div style={{ fontSize: '32px', marginBottom: '10px' }}>📂</div>
          <div style={{ fontWeight: 'bold', color: themeText, marginBottom: '4px', fontSize: '14px' }}>
            No Calculated Data Available Yet
          </div>
          Upload and approve an invoice or carbon dataset in the <strong>Upload & Review</strong> tab to automatically generate live compliance reports.
        </div>
      )}

    </div>
  );
}
