import React, { useState } from 'react';

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
  themeSubtext
}) {
  const [downloadingKey, setDownloadingKey] = useState(null);

  const hasCalculatedData = Boolean(
    universalResult &&
    universalResult.reports &&
    universalResult.records &&
    universalResult.records.length > 0
  );

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
      // Direct request to backend port 8000
      const targetUrl = reportUrl.startsWith('http') 
        ? reportUrl 
        : `http://localhost:8000${reportUrl.startsWith('/') ? '' : '/'}${reportUrl}`;

      const headers = getAuthHeaders ? getAuthHeaders() : {};
      const response = await fetch(targetUrl, {
        method: 'GET',
        headers: headers
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      // Determine filename from Content-Disposition header if available
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
      } else {
        alert(`Failed to download report: ${err.message}`);
      }
    } finally {
      setDownloadingKey(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Banner */}
      <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 6px 0', color: '#10b981' }}>
              📑 Enterprise Compliance & ESG Reports
            </h3>
            <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>
              Download verified carbon inventory workbooks, CBAM declarations, and audit packages.
            </p>
          </div>
          <span style={{ fontSize: '11px', padding: '6px 12px', borderRadius: '20px', backgroundColor: 'rgba(59,130,246,0.1)', color: '#60a5fa', fontWeight: '800' }}>
            Included with {currentSub?.plan_tier?.toUpperCase() || 'TRIAL'} Plan
          </span>
        </div>
      </div>

      {/* 4 Report Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
        {reportCards.map((rep, idx) => {
          const isDownloading = downloadingKey === rep.key;

          return (
            <div key={idx} style={{
              padding: '24px', borderRadius: '18px', backgroundColor: themeCard,
              border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column',
              justifyContent: 'space-between', minHeight: '260px'
            }}>
              <div>
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>{rep.icon}</div>
                <h4 style={{ fontSize: '15px', fontWeight: '800', margin: '0 0 4px 0', color: themeText }}>{rep.name}</h4>
                <div style={{ fontSize: '11px', color: '#10b981', fontWeight: 'bold', marginBottom: '8px' }}>{rep.type}</div>
                <p style={{ fontSize: '12px', color: themeSubtext, margin: '0 0 20px 0', lineHeight: 1.4 }}>{rep.desc}</p>
              </div>

              {hasCalculatedData ? (
                <button 
                  type="button"
                  id={`download-report-${rep.key}`}
                  onClick={(e) => handleDownload(e, rep)}
                  disabled={isDownloading}
                  style={{
                    padding: '11px 16px', borderRadius: '10px', 
                    backgroundColor: isDownloading ? '#059669' : '#10b981', 
                    color: '#080c14',
                    border: 'none',
                    cursor: isDownloading ? 'wait' : 'pointer',
                    fontWeight: '800', fontSize: '13px', textAlign: 'center',
                    boxShadow: '0 4px 12px rgba(16,185,129,0.3)', display: 'block',
                    width: '100%',
                    transition: 'all 0.2s ease'
                  }}>
                  {isDownloading ? '⏳ Downloading...' : '⬇️ Download Report'}
                </button>
              ) : (
                <button
                  type="button"
                  id={`download-report-disabled-${rep.key}`}
                  disabled
                  style={{
                    padding: '11px 16px', borderRadius: '10px',
                    backgroundColor: isDarkMode ? '#1f2937' : '#e2e8f0',
                    color: themeSubtext, border: 'none',
                    fontWeight: '700', fontSize: '12px', textAlign: 'center',
                    cursor: 'not-allowed', opacity: 0.7,
                    width: '100%'
                  }}>
                  🔒 No calculated data available yet
                </button>
              )}
            </div>
          );
        })}
      </div>

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


