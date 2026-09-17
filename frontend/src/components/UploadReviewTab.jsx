import React, { useRef, useState } from 'react';
import { API_BASE } from '../config';

export default function UploadReviewTab({
  currentUser,
  universalFile,
  setUniversalFile,
  universalStatus,
  setUniversalStatus,
  universalResult,
  setUniversalResult,
  universalUploadId,
  setUniversalUploadId,
  reviewedRecords,
  setReviewedRecords,
  setParserResponse,
  showToast,
  refreshUserData,
  fetchUserUploadData,
  fetchBillingAndActivity,
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
  const [errorMessage, setErrorMessage] = useState('');
  const [approvingState, setApprovingState] = useState('idle'); // 'idle' | 'approving' | 'success' | 'error'
  const activeUploadTimestampRef = useRef(0);
  const fileInputRef = useRef(null);

  // Clear single document
  const handleResetDocument = () => {
    activeUploadTimestampRef.current = Date.now();
    setUniversalFile(null);
    setUniversalStatus('idle');
    setUniversalUploadId('');
    setReviewedRecords([]);
    setParserResponse(null);
    setErrorMessage('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Immediate state reset when a new single file is chosen
  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0] ? e.target.files[0] : null;
    activeUploadTimestampRef.current = Date.now();
    setUniversalFile(file);
    setUniversalStatus('idle');
    setUniversalUploadId('');
    setReviewedRecords([]);
    setParserResponse(null);
    setErrorMessage('');
  };

  // Single Upload Handler
  const handleUniversalUpload = () => {
    if (!universalFile) return;
    if ((currentUser?.token_balance || 0) < 15) {
      setLowTokenDetails({ required: 15, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }

    const uploadTimestamp = Date.now();
    activeUploadTimestampRef.current = uploadTimestamp;
    
    setReviewedRecords([]);
    setUniversalUploadId('');
    setParserResponse(null);
    setErrorMessage('');
    setUniversalStatus('uploading');

    const formData = new FormData();
    formData.append('file', universalFile);

    fetch(`${API_BASE}/api/upload/universal`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('carbonledger_token')}` },
      body: formData
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (activeUploadTimestampRef.current !== uploadTimestamp) {
        return;
      }

      if (status === 402) {
        setLowTokenDetails({ required: 15, current: currentUser?.token_balance || 0 });
        setShowLowTokenModal(true);
        setUniversalStatus('idle');
        return;
      }
      if (status !== 200) {
        throw new Error(body.detail || 'Extraction failed');
      }

      const extracted = body.records || [];
      if (extracted.length === 0) {
        setUniversalUploadId(body.upload_id || '');
        setReviewedRecords([]);
        setParserResponse(body.parser_response || null);
        setUniversalStatus('empty');
        setErrorMessage('No reliable carbon activity records were extracted from this document.');
        showToast('Document processed: No transactional carbon activities found.');
      } else {
        setUniversalUploadId(body.upload_id);
        setReviewedRecords(extracted);
        setParserResponse(body.parser_response || null);
        setUniversalStatus('parsed');
        showToast(`Extracted ${extracted.length} real activity records from ${universalFile.name}!`);
      }
      refreshUserData();
      if (fetchBillingAndActivity) fetchBillingAndActivity();
    })
    .catch(err => {
      if (activeUploadTimestampRef.current !== uploadTimestamp) return;
      setUniversalStatus('error');
      setReviewedRecords([]);
      setUniversalUploadId('');
      setErrorMessage(err.message || 'Document processing failed.');
    });
  };

  const handleApproveAndCalculate = () => {
    if (!universalUploadId || reviewedRecords.length === 0 || approvingState === 'approving') return;
    if ((currentUser?.token_balance || 0) < 10) {
      setLowTokenDetails({ required: 10, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }

    setApprovingState('approving');

    fetch(`${API_BASE}/api/upload/approve`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ upload_id: universalUploadId, records: reviewedRecords })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (status === 402) {
        setApprovingState('idle');
        setLowTokenDetails({ required: 10, current: currentUser?.token_balance || 0 });
        setShowLowTokenModal(true);
        return;
      }
      if (status === 401) {
        setApprovingState('error');
        showToast('Your session has expired. Please sign in again.');
        return;
      }
      if (status === 422) {
        setApprovingState('error');
        showToast(body.detail || 'The extracted data requires correction before approval.');
        return;
      }
      if (status >= 500) {
        setApprovingState('error');
        showToast('Carbon calculation failed. Please try again.');
        return;
      }
      if (status !== 200) {
        setApprovingState('error');
        showToast(body.detail || 'Approval failed.');
        return;
      }

      setApprovingState('success');
      showToast('Document approved successfully. Carbon emissions calculated.');
      const normalizedResult = {
        ...body,
        records: body.records || body.inventory_records || [],
        status: 'calculated'
      };
      if (setUniversalResult) {
        setUniversalResult(normalizedResult);
      }
      if (fetchUserUploadData) fetchUserUploadData();
      refreshUserData();
      if (fetchBillingAndActivity) fetchBillingAndActivity();
      setTimeout(() => {
        setApprovingState('idle');
        setActiveTab('Dashboard');
      }, 300);
    })
    .catch(err => {
      setApprovingState('error');
      showToast(err.message || 'Carbon calculation failed. Please try again.');
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* SINGLE INVOICE UPLOAD PANEL */}
      <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 6px 0', color: '#10b981' }}>
              Upload Invoice
            </h3>
            <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>
              Select ONE PDF invoice to extract activity items, review emission factors, and approve audited calculations.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {universalFile && (
              <button
                onClick={handleResetDocument}
                style={{
                  fontSize: '12px', padding: '6px 14px', borderRadius: '8px',
                  backgroundColor: isDarkMode ? '#1f2937' : '#e2e8f0', color: themeText,
                  border: 'none', cursor: 'pointer', fontWeight: '600'
                }}>
                ✕ Clear Invoice
              </button>
            )}
            <span style={{ fontSize: '11px', padding: '6px 12px', borderRadius: '20px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', fontWeight: '800' }}>
              Supported: PDF • ⚡ 15 Tokens
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '14px', alignItems: 'center', marginTop: '20px', flexWrap: 'wrap' }}>
          <input 
            ref={fileInputRef}
            type="file" 
            multiple={false}
            onChange={handleFileChange}
            accept=".pdf"
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
            {universalStatus === 'uploading' ? 'Extracting Parameters...' : 'Upload & Extract (⚡ 15 Tokens)'}
          </button>
        </div>

        <div style={{ marginTop: '12px', fontSize: '12px', color: themeSubtext }}>
          {universalFile ? (
            <span>Selected Invoice: <strong style={{ color: themeText }}>{universalFile.name}</strong> ({(universalFile.size / 1024).toFixed(1)} KB)</span>
          ) : (
            <span>No file selected</span>
          )}
        </div>
      </div>

      {/* REAL-TIME SINGLE PIPELINE PROGRESS STATE */}
      {universalStatus === 'uploading' && (
        <div style={{
          padding: '36px 32px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}`,
          display: 'flex', flexDirection: 'column', gap: '20px', boxShadow: '0 8px 24px rgba(0,0,0,0.15)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                width: '38px', height: '38px', borderRadius: '50%',
                border: '3px solid rgba(16,185,129,0.2)', borderTopColor: '#10b981',
                animation: 'spin 1s linear infinite'
              }} />
              <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
              <div>
                <h4 style={{ margin: '0 0 4px 0', color: themeText, fontSize: '16px', fontWeight: '800' }}>
                  Processing document...
                </h4>
                <p style={{ margin: 0, fontSize: '12px', color: themeSubtext }}>
                  Extracting invoice parameters, line item quantities, and matching authoritative GHG factors.
                </p>
              </div>
            </div>
            <span style={{ fontSize: '12px', padding: '6px 14px', borderRadius: '20px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', fontWeight: '700' }}>
              Pipeline Active
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginTop: '6px' }}>
            {[
              { step: '1. Receive & Parse', desc: 'Reading PDF tokens & tables', icon: '📑' },
              { step: '2. Classify & Segment', desc: 'Materials, Fuels, Freight, Utilities', icon: '🔍' },
              { step: '3. Extract & Normalize', desc: 'Physical quantities & units', icon: '⚡' },
              { step: '4. Validate & Match', desc: 'GHG Protocol & CBAM factors', icon: '🌿' }
            ].map((st, i) => (
              <div key={i} style={{
                padding: '14px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc',
                border: `1px solid ${themeBorder}`, display: 'flex', gap: '10px', alignItems: 'center'
              }}>
                <span style={{ fontSize: '18px' }}>{st.icon}</span>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '700', color: themeText }}>{st.step}</div>
                  <div style={{ fontSize: '11px', color: themeSubtext }}>{st.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ERROR STATE */}
      {universalStatus === 'error' && (
        <div style={{
          padding: '24px', borderRadius: '18px', backgroundColor: 'rgba(239,68,68,0.08)',
          border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444'
        }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <span style={{ fontSize: '20px' }}>⚠️</span>
            <div>
              <h4 style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '800' }}>Extraction Failed</h4>
              <p style={{ margin: 0, fontSize: '12px' }}>{errorMessage || 'Unable to extract data from the uploaded file.'}</p>
            </div>
          </div>
        </div>
      )}

      {/* EMPTY RESULT STATE */}
      {universalStatus === 'empty' && (
        <div style={{
          padding: '40px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}`,
          textAlign: 'center', color: themeSubtext
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>📄</div>
          <h4 style={{ margin: '0 0 6px 0', color: themeText, fontSize: '15px' }}>No Carbon Activity Data Found</h4>
          <p style={{ margin: 0, fontSize: '12px' }}>
            No reliable material, fuel, electricity, or logistics transaction rows were identified in this document.
          </p>
        </div>
      )}

      {/* IDLE / NO DOCUMENT STATE */}
      {universalStatus === 'idle' && reviewedRecords.length === 0 && (
        <div style={{
          padding: '48px', borderRadius: '18px', backgroundColor: themeCard, border: `1px dashed ${themeBorder}`,
          textAlign: 'center', color: themeSubtext
        }}>
          <div style={{ fontSize: '36px', marginBottom: '10px' }}>📄</div>
          <h4 style={{ margin: '0 0 6px 0', color: themeText, fontSize: '15px', fontWeight: '700' }}>
            No invoice uploaded
          </h4>
          <p style={{ margin: 0, fontSize: '12px', maxWidth: '420px', marginInline: 'auto' }}>
            Upload a single PDF invoice above to extract line items, review factor matching, and calculate audited emissions.
          </p>
        </div>
      )}

      {/* REVIEW & APPROVAL TABLE */}
      {reviewedRecords && reviewedRecords.length > 0 && universalStatus !== 'uploading' && (
        <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '17px', fontWeight: '800', margin: 0, color: themeText }}>
                📋 Line Items Review & Audit Parity ({reviewedRecords.length} real records)
              </h3>
              <p style={{ fontSize: '12px', color: themeSubtext, margin: '4px 0 0' }}>
                Extracted directly via Document AI model without placeholder or fallback values. Ready for Review.
              </p>
            </div>
            <button 
              disabled={approvingState === 'approving'}
              onClick={handleApproveAndCalculate}
              style={{
                padding: '11px 24px', borderRadius: '10px',
                backgroundColor: approvingState === 'success' ? '#10b981' : (approvingState === 'error' ? '#ef4444' : '#3b82f6'),
                color: '#fff', border: 'none', fontWeight: '800',
                cursor: approvingState === 'approving' ? 'not-allowed' : 'pointer',
                opacity: approvingState === 'approving' ? 0.7 : 1,
                fontSize: '13px', boxShadow: '0 4px 12px rgba(59,130,246,0.3)',
                display: 'flex', alignItems: 'center', gap: '8px'
              }}>
              {approvingState === 'approving' && '⏳ Approving & Calculating...'}
              {approvingState === 'success' && '✓ Approved & Calculated'}
              {approvingState === 'error' && '⚠️ Retry Approval & Calculate'}
              {approvingState === 'idle' && 'Approve & Calculate (⚡ 10 Tokens)'}
            </button>
          </div>

          {/* Status Breakdown Metrics */}
          {(() => {
            const counts = {
              ready: 0,
              review: 0,
              notFound: 0,
              missing: 0,
              reference: 0
            };
            reviewedRecords.forEach(r => {
              const s = String(r.calculation_status || (r.carbon_calculation?.calculation_ready ? 'READY' : 'REVIEW_REQUIRED')).toUpperCase();
              if (s === 'READY' || s === 'CALCULATED') counts.ready++;
              else if (s === 'FACTOR_NOT_FOUND') counts.notFound++;
              else if (s === 'MISSING_REQUIRED_DATA') counts.missing++;
              else if (s === 'REFERENCE_ONLY') counts.reference++;
              else counts.review++;
            });

            return (
              <div style={{ display: 'flex', gap: '10px', marginBottom: '18px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '12px', padding: '5px 12px', borderRadius: '8px', backgroundColor: 'rgba(16,185,129,0.15)', color: '#10b981', fontWeight: '700' }}>
                  ✓ {counts.ready} Ready to Calculate
                </span>
                {counts.review > 0 && (
                  <span style={{ fontSize: '12px', padding: '5px 12px', borderRadius: '8px', backgroundColor: 'rgba(234,179,8,0.15)', color: '#eab308', fontWeight: '700' }}>
                    ⚠️ {counts.review} Review Required
                  </span>
                )}
                {counts.notFound > 0 && (
                  <span style={{ fontSize: '12px', padding: '5px 12px', borderRadius: '8px', backgroundColor: 'rgba(249,115,22,0.15)', color: '#f97316', fontWeight: '700' }}>
                    ✕ {counts.notFound} Factor Not Found
                  </span>
                )}
                {counts.missing > 0 && (
                  <span style={{ fontSize: '12px', padding: '5px 12px', borderRadius: '8px', backgroundColor: 'rgba(239,68,68,0.15)', color: '#ef4444', fontWeight: '700' }}>
                    ❓ {counts.missing} Missing Required Data
                  </span>
                )}
                {counts.reference > 0 && (
                  <span style={{ fontSize: '12px', padding: '5px 12px', borderRadius: '8px', backgroundColor: 'rgba(148,163,184,0.15)', color: '#94a3b8', fontWeight: '700' }}>
                    ℹ️ {counts.reference} Reference Only (PO Guard)
                  </span>
                )}
              </div>
            );
          })()}

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', whiteSpace: 'nowrap' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, textTransform: 'uppercase' }}>
                  <th style={{ padding: '10px 8px' }}>#</th>
                  <th style={{ padding: '10px 8px' }}>Material / Commodity</th>
                  <th style={{ padding: '10px 8px' }}>Supplier</th>
                  <th style={{ padding: '10px 8px' }}>Supplier ID</th>
                  <th style={{ padding: '10px 8px' }}>Quantity</th>
                  <th style={{ padding: '10px 8px' }}>Unit</th>
                  <th style={{ padding: '10px 8px' }}>Weight</th>
                  <th style={{ padding: '10px 8px' }}>Weight Unit</th>
                  <th style={{ padding: '10px 8px' }}>Activity Type</th>
                  <th style={{ padding: '10px 8px' }}>Scope</th>
                  <th style={{ padding: '10px 8px' }}>Fuel Type</th>
                  <th style={{ padding: '10px 8px' }}>Energy Type</th>
                  <th style={{ padding: '10px 8px' }}>Distance</th>
                  <th style={{ padding: '10px 8px' }}>Distance Unit</th>
                  <th style={{ padding: '10px 8px' }}>Origin</th>
                  <th style={{ padding: '10px 8px' }}>Destination</th>
                  <th style={{ padding: '10px 8px' }}>Transport Mode</th>
                  <th style={{ padding: '10px 8px' }}>Consumption</th>
                  <th style={{ padding: '10px 8px' }}>Consumption Unit</th>
                  <th style={{ padding: '10px 8px' }}>Country</th>
                  <th style={{ padding: '10px 8px' }}>Facility</th>
                  <th style={{ padding: '10px 8px' }}>Emission Factor</th>
                  <th style={{ padding: '10px 8px' }}>Factor Unit</th>
                  <th style={{ padding: '10px 8px' }}>Factor Source</th>
                  <th style={{ padding: '10px 8px' }}>Calculation Status</th>
                </tr>
              </thead>
              <tbody>
                {reviewedRecords.map((r, i) => {
                  const material = r.activity?.material || r.activity?.product || r.material;
                  const supplier = r.supplier?.name || (typeof r.supplier === 'string' ? r.supplier : null);
                  const supplierId = r.supplier?.supplier_id || r.supplier_id;
                  const quantity = r.activity?.quantity !== undefined && r.activity?.quantity !== null ? r.activity.quantity : (r.quantity !== undefined ? r.quantity : null);
                  const unit = r.activity?.unit || r.unit;
                  const weight = r.activity?.weight !== undefined && r.activity?.weight !== null ? r.activity.weight : (r.weight !== undefined ? r.weight : null);
                  const weightUnit = r.activity?.weight_unit || r.weight_unit;
                  const activityType = r.activity?.activity_type || r.activity_type || 'PURCHASED_GOODS';
                  const scope = r.activity?.scope || r.scope || 'SCOPE_3';
                  const fuelType = r.activity?.fuel_type || r.fuel_type;
                  const energyType = r.activity?.energy_type || r.energy_type;
                  const distance = r.activity?.distance !== undefined && r.activity?.distance !== null ? r.activity.distance : (r.distance !== undefined ? r.distance : null);
                  const distanceUnit = r.activity?.distance_unit || r.distance_unit;
                  const origin = r.activity?.origin || r.origin;
                  const destination = r.activity?.destination || r.destination;
                  const transportMode = r.activity?.transport_mode || r.transport_mode;
                  const consumption = r.activity?.consumption !== undefined && r.activity?.consumption !== null ? r.activity.consumption : (r.consumption !== undefined ? r.consumption : null);
                  const consumptionUnit = r.activity?.consumption_unit || r.consumption_unit;
                  const country = r.company?.country || r.supplier?.country || r.country;
                  const facility = r.company?.facility || r.facility;

                  // Emission factor fields
                  let efVal = null;
                  let efUnit = null;
                  let efSource = null;

                  if (r.emission_factor && typeof r.emission_factor === 'object') {
                    efVal = r.emission_factor.value ?? r.emission_factor.factor_value ?? null;
                    efUnit = r.emission_factor.unit ?? r.emission_factor.factor_unit ?? null;
                    efSource = r.emission_factor.source ?? r.emission_factor.source_sheet ?? null;
                  } else if (typeof r.emission_factor === 'number' || typeof r.emission_factor === 'string') {
                    efVal = r.emission_factor;
                    efUnit = r.factor_unit || null;
                    efSource = r.factor_source || null;
                  }

                  const calcStatus = String(r.calculation_status || (r.carbon_calculation?.calculation_ready ? 'READY' : 'REVIEW_REQUIRED')).toUpperCase();
                  const reviewReason = r.review_reason || r.carbon_calculation?.reason || r.anomaly_reason;

                  const renderCell = (val, isKey = false) => {
                    if (val === null || val === undefined || val === '' || val === 'None') {
                      return <span style={{ color: themeSubtext, fontStyle: 'italic' }}>—</span>;
                    }
                    if (typeof val === 'object') {
                      return <span style={{ color: themeSubtext, fontStyle: 'italic' }}>—</span>;
                    }
                    return <span style={isKey ? { fontWeight: '700', color: '#10b981' } : {}}>{String(val)}</span>;
                  };

                  let statusBadgeStyle = {
                    padding: '3px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold'
                  };
                  let statusLabel = 'Review Required';

                  if (calcStatus === 'READY') {
                    statusBadgeStyle.backgroundColor = 'rgba(16,185,129,0.15)';
                    statusBadgeStyle.color = '#10b981';
                    statusLabel = 'Ready';
                  } else if (calcStatus === 'CALCULATED') {
                    statusBadgeStyle.backgroundColor = 'rgba(16,185,129,0.15)';
                    statusBadgeStyle.color = '#10b981';
                    statusLabel = 'Calculated';
                  } else if (calcStatus === 'FACTOR_NOT_FOUND') {
                    statusBadgeStyle.backgroundColor = 'rgba(249,115,22,0.15)';
                    statusBadgeStyle.color = '#f97316';
                    statusLabel = 'Factor Not Found';
                  } else if (calcStatus === 'MISSING_REQUIRED_DATA') {
                    statusBadgeStyle.backgroundColor = 'rgba(239,68,68,0.15)';
                    statusBadgeStyle.color = '#ef4444';
                    statusLabel = 'Missing Data';
                  } else if (calcStatus === 'REFERENCE_ONLY') {
                    statusBadgeStyle.backgroundColor = 'rgba(148,163,184,0.15)';
                    statusBadgeStyle.color = '#94a3b8';
                    statusLabel = 'Reference Only';
                  } else {
                    statusBadgeStyle.backgroundColor = 'rgba(234,179,8,0.15)';
                    statusBadgeStyle.color = '#eab308';
                    statusLabel = 'Review Required';
                  }

                  return (
                    <tr key={i} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                      <td style={{ padding: '10px 8px', color: themeSubtext }}>{i + 1}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(material, true)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(supplier)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(supplierId)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(quantity, true)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(unit)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(weight)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(weightUnit)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(activityType)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(scope)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(fuelType)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(energyType)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(distance)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(distanceUnit)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(origin)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(destination)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(transportMode)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(consumption)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(consumptionUnit)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(country)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(facility)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(efVal)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(efUnit)}</td>
                      <td style={{ padding: '10px 8px' }}>{renderCell(efSource)}</td>
                      <td style={{ padding: '10px 8px' }}>
                        <span style={statusBadgeStyle} title={reviewReason || ''}>
                          {statusLabel}
                        </span>
                        {(calcStatus === 'REVIEW_REQUIRED' || calcStatus === 'FACTOR_NOT_FOUND' || calcStatus === 'MISSING_REQUIRED_DATA') && reviewReason && (
                          <div style={{ fontSize: '10px', color: statusBadgeStyle.color, marginTop: '2px', maxWidth: '240px', whiteSpace: 'normal', lineHeight: '1.2' }}>
                            {reviewReason}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}
