import React from 'react';

export default function UploadReviewTab({
  currentUser,
  universalFile,
  setUniversalFile,
  universalStatus,
  setUniversalStatus,
  universalUploadId,
  setUniversalUploadId,
  reviewedRecords,
  setReviewedRecords,
  setParserResponse,
  showToast,
  refreshUserData,
  fetchUserUploadData,
  setActiveTab,
  setLowTokenDetails,
  setShowLowTokenModal,
  getAuthHeaders,
  isDarkMode,
  themeCard,
  themeBorder,
  themeText,
  themeSubtext
}) {
  const handleUniversalUpload = () => {
    if (!universalFile) return;
    if ((currentUser?.token_balance || 0) < 15) {
      setLowTokenDetails({ required: 15, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }
    const formData = new FormData();
    formData.append('file', universalFile);
    setUniversalStatus('uploading');

    fetch('http://localhost:8000/api/upload/universal', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('carbonledger_token')}` },
      body: formData
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (status === 402) {
        setLowTokenDetails({ required: 15, current: currentUser?.token_balance || 0 });
        setShowLowTokenModal(true);
        setUniversalStatus('idle');
        return;
      }
      if (status !== 200) throw new Error(body.detail || 'Upload failed');
      setUniversalUploadId(body.upload_id);
      setReviewedRecords(body.records || []);
      setParserResponse(body.parser_response || null);
      setUniversalStatus('parsed');
      showToast('Document parsed successfully! Please review extracted line items.');
      refreshUserData();
    })
    .catch(err => {
      setUniversalStatus('error');
      alert(err.message);
    });
  };

  const handleApproveAndCalculate = () => {
    if ((currentUser?.token_balance || 0) < 10) {
      setLowTokenDetails({ required: 10, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }
    fetch('http://localhost:8000/api/upload/approve', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ upload_id: universalUploadId, records: reviewedRecords })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (status === 402) {
        setLowTokenDetails({ required: 10, current: currentUser?.token_balance || 0 });
        setShowLowTokenModal(true);
        return;
      }
      if (status !== 200) throw new Error(body.detail || 'Calculation failed');
      showToast('Calculations approved and compliance reports generated!');
      fetchUserUploadData();
      refreshUserData();
      setActiveTab('Dashboard');
    })
    .catch(err => alert(err.message));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Upload Zone */}
      <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 6px 0', color: '#10b981' }}>
              📤 Universal Document Intake Pipeline
            </h3>
            <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>
              Upload invoices, purchase orders, utility bills, or shipping manifests (PDF, Excel, CSV, JSON, ZIP).
            </p>
          </div>
          <span style={{ fontSize: '11px', padding: '6px 12px', borderRadius: '20px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', fontWeight: '800' }}>
            ⚡ Token Cost: 15 Tokens
          </span>
        </div>

        <div style={{ display: 'flex', gap: '14px', alignItems: 'center', marginTop: '20px' }}>
          <input 
            type="file" 
            onChange={e => setUniversalFile(e.target.files[0])}
            style={{ fontSize: '13px', color: themeText, padding: '8px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff' }}
          />
          <button 
            disabled={!universalFile || universalStatus === 'uploading'}
            onClick={handleUniversalUpload}
            style={{
              padding: '11px 24px', borderRadius: '10px', backgroundColor: '#10b981', color: '#080c14',
              border: 'none', fontWeight: '800', cursor: (!universalFile || universalStatus === 'uploading') ? 'not-allowed' : 'pointer',
              opacity: (!universalFile || universalStatus === 'uploading') ? 0.6 : 1,
              boxShadow: '0 4px 12px rgba(16,185,129,0.3)', fontSize: '13px'
            }}>
            {universalStatus === 'uploading' ? 'Extracting Parameters...' : 'Parse Document (⚡ 15 Tokens)'}
          </button>
        </div>
      </div>

      {/* REVIEW & APPROVAL TABLE */}
      {reviewedRecords && reviewedRecords.length > 0 && (
        <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '17px', fontWeight: '800', margin: 0, color: themeText }}>
                📋 Line Items Review & Audit Parity
              </h3>
              <p style={{ fontSize: '12px', color: themeSubtext, margin: '4px 0 0' }}>
                Review extracted parameters before final carbon footprint calculations.
              </p>
            </div>
            <button 
              onClick={handleApproveAndCalculate}
              style={{
                padding: '11px 24px', borderRadius: '10px', backgroundColor: '#3b82f6', color: '#fff',
                border: 'none', fontWeight: '800', cursor: 'pointer', fontSize: '13px',
                boxShadow: '0 4px 12px rgba(59,130,246,0.3)'
              }}>
              Approve & Calculate (⚡ 10 Tokens)
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, textTransform: 'uppercase' }}>
                  <th style={{ padding: '10px 8px' }}>Material / Commodity</th>
                  <th style={{ padding: '10px 8px' }}>Supplier</th>
                  <th style={{ padding: '10px 8px' }}>Quantity</th>
                  <th style={{ padding: '10px 8px' }}>Unit</th>
                  <th style={{ padding: '10px 8px' }}>Cost</th>
                  <th style={{ padding: '10px 8px' }}>Country</th>
                </tr>
              </thead>
              <tbody>
                {reviewedRecords.map((r, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                    <td style={{ padding: '10px 8px', fontWeight: 'bold', color: '#10b981' }}>{r.material}</td>
                    <td style={{ padding: '10px 8px' }}>{r.supplier || 'N/A'}</td>
                    <td style={{ padding: '10px 8px', fontWeight: 'bold' }}>{r.quantity}</td>
                    <td style={{ padding: '10px 8px' }}>{r.unit}</td>
                    <td style={{ padding: '10px 8px' }}>€{r.cost || 0}</td>
                    <td style={{ padding: '10px 8px' }}>{r.country || 'DE'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}

