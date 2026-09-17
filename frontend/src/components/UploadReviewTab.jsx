import React, { useRef, useState, useEffect } from 'react';
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
  // Mode: 'single' | 'bulk'
  const [uploadMode, setUploadMode] = useState('single');
  const [errorMessage, setErrorMessage] = useState('');
  const activeUploadTimestampRef = useRef(0);

  // Bulk Upload States
  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkBatchId, setBulkBatchId] = useState(null);
  const [bulkBatchData, setBulkBatchData] = useState(null);
  const [bulkUploading, setBulkUploading] = useState(false);
  const pollingTimerRef = useRef(null);

  // Formatting helpers
  const formatSeconds = (sec) => {
    if (sec === null || sec === undefined || isNaN(sec)) return '00:00:00';
    const s = Math.max(0, Math.floor(sec));
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = s % 60;
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const formatEstTime = (sec) => {
    if (sec === null || sec === undefined || isNaN(sec)) return 'Estimating...';
    const s = Math.max(0, Math.round(sec));
    if (s < 60) return `${s}s remaining`;
    const mins = Math.floor(s / 60);
    const remainder = s % 60;
    return `${mins}m ${remainder}s remaining`;
  };

  // Poll bulk batch status
  useEffect(() => {
    if (!bulkBatchId) return;

    const pollBatch = async () => {
      try {
        const token = localStorage.getItem('carbonledger_token');
        const res = await fetch(`${API_BASE}/api/upload/batch/${bulkBatchId}`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (!res.ok) return;
        const data = await res.json();
        setBulkBatchData(data);

        if (data.status === 'COMPLETED' || data.status === 'COMPLETED_WITH_REVIEW' || data.status === 'FAILED') {
          setBulkUploading(false);
          if (pollingTimerRef.current) {
            clearInterval(pollingTimerRef.current);
            pollingTimerRef.current = null;
          }
          if (refreshUserData) refreshUserData();
          if (fetchUserUploadData) fetchUserUploadData();
          if (fetchBillingAndActivity) fetchBillingAndActivity();
          if (showToast) {
            showToast(`Batch processing ${data.status.toLowerCase().replace('_', ' ')}: ${data.completed_count}/${data.total_documents} documents processed.`);
          }
        }
      } catch (e) {
        console.error('Batch polling error:', e);
      }
    };

    // Initial poll immediately
    pollBatch();
    pollingTimerRef.current = setInterval(pollBatch, 1000);

    return () => {
      if (pollingTimerRef.current) {
        clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
      }
    };
  }, [bulkBatchId]);

  // Clear single document
  const handleResetDocument = () => {
    activeUploadTimestampRef.current = Date.now();
    setUniversalFile(null);
    setUniversalStatus('idle');
    setUniversalUploadId('');
    setReviewedRecords([]);
    setParserResponse(null);
    setErrorMessage('');
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

  // Bulk File Change Handler
  const handleBulkFileChange = (e) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    setBulkFiles(files);
  };

  // Bulk Upload Start Handler
  const handleBulkUpload = () => {
    if (!bulkFiles || bulkFiles.length === 0) return;
    const requiredTokens = bulkFiles.length * 15;
    if ((currentUser?.token_balance || 0) < requiredTokens) {
      setLowTokenDetails({ required: requiredTokens, current: currentUser?.token_balance || 0 });
      setShowLowTokenModal(true);
      return;
    }

    setBulkUploading(true);
    setBulkBatchData(null);
    setBulkBatchId(null);

    const formData = new FormData();
    bulkFiles.forEach(file => {
      formData.append('files', file);
    });

    fetch(`${API_BASE}/api/upload/bulk`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${localStorage.getItem('carbonledger_token')}` },
      body: formData
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      if (status === 402) {
        setLowTokenDetails({ required: requiredTokens, current: currentUser?.token_balance || 0 });
        setShowLowTokenModal(true);
        setBulkUploading(false);
        return;
      }
      if (status !== 200) {
        throw new Error(body.detail || 'Bulk upload failed to initiate');
      }

      setBulkBatchId(body.batch_id);
      showToast(`Bulk processing started for ${body.total_files} files.`);
      refreshUserData();
      if (fetchBillingAndActivity) fetchBillingAndActivity();
    })
    .catch(err => {
      setBulkUploading(false);
      showToast(err.message || 'Bulk upload failed.');
    });
  };

  const [approvingState, setApprovingState] = useState('idle'); // 'idle' | 'approving' | 'success' | 'error'

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

  // Inspect a specific job's records in the review table
  const handleInspectJob = (job) => {
    if (job.records && job.records.length > 0) {
      setUniversalUploadId(job.upload_id || `job-${job.job_id}`);
      setReviewedRecords(job.records);
      setUniversalStatus('parsed');
      showToast(`Loaded ${job.records.length} records from ${job.filename} for inspection.`);
    } else {
      showToast(`No extracted records available for ${job.filename}.`);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Mode Switcher Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: `1px solid ${themeBorder}`, paddingBottom: '12px' }}>
        <button
          onClick={() => setUploadMode('single')}
          style={{
            padding: '10px 20px', borderRadius: '10px', fontSize: '13px', fontWeight: '800',
            border: 'none', cursor: 'pointer', transition: 'all 0.2s ease',
            backgroundColor: uploadMode === 'single' ? '#10b981' : (isDarkMode ? '#1f2937' : '#e2e8f0'),
            color: uploadMode === 'single' ? '#080c14' : themeText,
            boxShadow: uploadMode === 'single' ? '0 4px 12px rgba(16,185,129,0.3)' : 'none'
          }}>
          📄 Single Invoice / Document
        </button>
        <button
          onClick={() => setUploadMode('bulk')}
          style={{
            padding: '10px 20px', borderRadius: '10px', fontSize: '13px', fontWeight: '800',
            border: 'none', cursor: 'pointer', transition: 'all 0.2s ease',
            backgroundColor: uploadMode === 'bulk' ? '#10b981' : (isDarkMode ? '#1f2937' : '#e2e8f0'),
            color: uploadMode === 'bulk' ? '#080c14' : themeText,
            boxShadow: uploadMode === 'bulk' ? '0 4px 12px rgba(16,185,129,0.3)' : 'none',
            display: 'flex', alignItems: 'center', gap: '6px'
          }}>
          📚 Bulk Batch Upload (Multi-File)
          <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '10px', backgroundColor: uploadMode === 'bulk' ? '#080c14' : '#10b981', color: uploadMode === 'bulk' ? '#10b981' : '#080c14', fontWeight: '900' }}>
            NEW
          </span>
        </button>
      </div>

      {/* SINGLE UPLOAD MODE */}
      {uploadMode === 'single' && (
        <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 6px 0', color: '#10b981' }}>
                📤 Universal Document Intake Pipeline
              </h3>
              <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>
                Upload invoices, purchase orders, utility bills, or shipping manifests (PDF, Excel, CSV).
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
                  ✕ Clear Document
                </button>
              )}
              <span style={{ fontSize: '11px', padding: '6px 12px', borderRadius: '20px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', fontWeight: '800' }}>
                ⚡ Token Cost: 15 Tokens
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '14px', alignItems: 'center', marginTop: '20px', flexWrap: 'wrap' }}>
            <input 
              type="file" 
              key={universalUploadId || 'file-input'}
              onChange={handleFileChange}
              accept=".pdf,.xlsx,.xls,.csv,.json,.zip"
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

          {universalFile && (
            <div style={{ marginTop: '12px', fontSize: '12px', color: themeSubtext }}>
              Selected Document: <strong style={{ color: themeText }}>{universalFile.name}</strong> ({(universalFile.size / 1024).toFixed(1)} KB)
            </div>
          )}
        </div>
      )}

      {/* BULK UPLOAD MODE */}
      {uploadMode === 'bulk' && (
        <div style={{ padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '800', margin: '0 0 6px 0', color: '#10b981' }}>
                📚 Asynchronous Multi-Format Bulk Intake Pipeline
              </h3>
              <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>
                Select and upload dozens of invoices simultaneously across formats A–J. AI processes in parallel with live estimation.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              {bulkFiles.length > 0 && (
                <button
                  onClick={() => { setBulkFiles([]); setBulkBatchData(null); setBulkBatchId(null); }}
                  style={{
                    fontSize: '12px', padding: '6px 14px', borderRadius: '8px',
                    backgroundColor: isDarkMode ? '#1f2937' : '#e2e8f0', color: themeText,
                    border: 'none', cursor: 'pointer', fontWeight: '600'
                  }}>
                  ✕ Clear Batch
                </button>
              )}
              <span style={{ fontSize: '11px', padding: '6px 12px', borderRadius: '20px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', fontWeight: '800' }}>
                ⚡ Cost: 15 Tokens / File
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '14px', alignItems: 'center', marginTop: '20px', flexWrap: 'wrap' }}>
            <input 
              type="file" 
              multiple
              onChange={handleBulkFileChange}
              accept=".pdf,.xlsx,.xls,.csv"
              style={{ fontSize: '13px', color: themeText, padding: '8px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff' }}
            />
            <button 
              disabled={bulkFiles.length === 0 || bulkUploading}
              onClick={handleBulkUpload}
              style={{
                padding: '11px 24px', borderRadius: '10px', backgroundColor: '#10b981', color: '#080c14',
                border: 'none', fontWeight: '800', cursor: (bulkFiles.length === 0 || bulkUploading) ? 'not-allowed' : 'pointer',
                opacity: (bulkFiles.length === 0 || bulkUploading) ? 0.6 : 1,
                boxShadow: '0 4px 12px rgba(16,185,129,0.3)', fontSize: '13px'
              }}>
              {bulkUploading ? 'Processing Batch...' : `Start Bulk Processing (${bulkFiles.length} files • ⚡ ${bulkFiles.length * 15} Tokens)`}
            </button>
          </div>

          {bulkFiles.length > 0 && (
            <div style={{ marginTop: '14px', fontSize: '12px', color: themeSubtext, display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <span>Total Selected: <strong style={{ color: themeText }}>{bulkFiles.length} documents</strong></span>
              <span>Total Size: <strong style={{ color: themeText }}>{(bulkFiles.reduce((acc, f) => acc + f.size, 0) / 1024).toFixed(1)} KB</strong></span>
            </div>
          )}
        </div>
      )}

      {/* LIVE BULK BATCH PROGRESS & TIMER PANEL */}
      {bulkBatchData && (
        <div style={{
          padding: '28px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}`,
          display: 'flex', flexDirection: 'column', gap: '20px', boxShadow: '0 8px 24px rgba(0,0,0,0.15)'
        }}>
          {/* Header & Status */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '800', color: themeText }}>
                  🚀 Batch Execution Session: <span style={{ fontFamily: 'monospace', color: '#10b981' }}>{bulkBatchData.batch_id}</span>
                </h4>
                <span style={{
                  fontSize: '11px', padding: '4px 10px', borderRadius: '12px', fontWeight: '800',
                  backgroundColor: bulkBatchData.status === 'COMPLETED' ? 'rgba(16,185,129,0.15)' :
                                   bulkBatchData.status === 'COMPLETED_WITH_REVIEW' ? 'rgba(234,179,8,0.15)' :
                                   bulkBatchData.status === 'FAILED' ? 'rgba(239,68,68,0.15)' : 'rgba(59,130,246,0.15)',
                  color: bulkBatchData.status === 'COMPLETED' ? '#10b981' :
                         bulkBatchData.status === 'COMPLETED_WITH_REVIEW' ? '#eab308' :
                         bulkBatchData.status === 'FAILED' ? '#ef4444' : '#3b82f6'
                }}>
                  {bulkBatchData.status}
                </span>
              </div>
              <p style={{ margin: '4px 0 0', fontSize: '12px', color: themeSubtext }}>
                Live backend execution metrics derived from ISO timestamps.
              </p>
            </div>

            {/* Direct Dashboard Nav Button upon completion */}
            {(bulkBatchData.status === 'COMPLETED' || bulkBatchData.status === 'COMPLETED_WITH_REVIEW') && (
              <button
                onClick={() => {
                  if (fetchUserUploadData) fetchUserUploadData();
                  if (refreshUserData) refreshUserData();
                  setActiveTab('Dashboard');
                }}
                style={{
                  padding: '10px 20px', borderRadius: '10px', backgroundColor: '#10b981', color: '#080c14',
                  border: 'none', fontWeight: '800', cursor: 'pointer', fontSize: '13px',
                  boxShadow: '0 4px 14px rgba(16,185,129,0.4)', display: 'flex', alignItems: 'center', gap: '8px'
                }}>
                📊 View in Dashboard (Aggregated Total) →
              </button>
            )}
          </div>

          {/* Timers & Counters Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '14px' }}>
            <div style={{ padding: '14px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
              <div style={{ fontSize: '11px', color: themeSubtext, fontWeight: '700', textTransform: 'uppercase' }}>⏱️ Elapsed Time</div>
              <div style={{ fontSize: '20px', fontWeight: '900', color: themeText, marginTop: '4px', fontFamily: 'monospace' }}>
                {formatSeconds(bulkBatchData.elapsed_seconds)}
              </div>
            </div>

            <div style={{ padding: '14px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
              <div style={{ fontSize: '11px', color: themeSubtext, fontWeight: '700', textTransform: 'uppercase' }}>⏳ Estimated Remaining</div>
              <div style={{ fontSize: '15px', fontWeight: '800', color: '#3b82f6', marginTop: '6px' }}>
                {bulkBatchData.status === 'COMPLETED' || bulkBatchData.status === 'COMPLETED_WITH_REVIEW' ? 'Done' : formatEstTime(bulkBatchData.estimated_remaining_seconds)}
              </div>
            </div>

            <div style={{ padding: '14px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
              <div style={{ fontSize: '11px', color: themeSubtext, fontWeight: '700', textTransform: 'uppercase' }}>📑 Total Processed</div>
              <div style={{ fontSize: '20px', fontWeight: '900', color: themeText, marginTop: '4px' }}>
                {bulkBatchData.processed_documents} / {bulkBatchData.total_documents}
              </div>
            </div>

            <div style={{ padding: '14px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
              <div style={{ fontSize: '11px', color: '#10b981', fontWeight: '700', textTransform: 'uppercase' }}>✓ Completed</div>
              <div style={{ fontSize: '20px', fontWeight: '900', color: '#10b981', marginTop: '4px' }}>
                {bulkBatchData.completed_count}
              </div>
            </div>

            <div style={{ padding: '14px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
              <div style={{ fontSize: '11px', color: '#eab308', fontWeight: '700', textTransform: 'uppercase' }}>⚠️ Review Required</div>
              <div style={{ fontSize: '20px', fontWeight: '900', color: '#eab308', marginTop: '4px' }}>
                {bulkBatchData.review_required_count}
              </div>
            </div>

            <div style={{ padding: '14px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', border: `1px solid ${themeBorder}` }}>
              <div style={{ fontSize: '11px', color: '#ef4444', fontWeight: '700', textTransform: 'uppercase' }}>✕ Failed</div>
              <div style={{ fontSize: '20px', fontWeight: '900', color: '#ef4444', marginTop: '4px' }}>
                {bulkBatchData.failed_count}
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: '700', marginBottom: '6px' }}>
              <span style={{ color: themeText }}>
                {bulkBatchData.current_file_name ? `Currently parsing: ${bulkBatchData.current_file_name}` : 'Batch Completion Progress'}
              </span>
              <span style={{ color: '#10b981' }}>{bulkBatchData.progress_pct}%</span>
            </div>
            <div style={{ width: '100%', height: '10px', borderRadius: '5px', backgroundColor: isDarkMode ? '#1f2937' : '#e2e8f0', overflow: 'hidden' }}>
              <div style={{
                width: `${bulkBatchData.progress_pct}%`, height: '100%',
                backgroundColor: bulkBatchData.failed_count > 0 && bulkBatchData.completed_count === 0 ? '#ef4444' : '#10b981',
                transition: 'width 0.4s ease'
              }} />
            </div>
          </div>

          {/* Per-Invoice Detail Status Table */}
          {bulkBatchData.jobs && bulkBatchData.jobs.length > 0 && (
            <div style={{ marginTop: '10px' }}>
              <h5 style={{ fontSize: '13px', fontWeight: '800', margin: '0 0 10px', color: themeText }}>
                Document Queue Breakdown ({bulkBatchData.jobs.length} Invoices)
              </h5>
              <div style={{ overflowX: 'auto', border: `1px solid ${themeBorder}`, borderRadius: '10px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', whiteSpace: 'nowrap' }}>
                  <thead>
                    <tr style={{ backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc', borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext }}>
                      <th style={{ padding: '8px 12px' }}>#</th>
                      <th style={{ padding: '8px 12px' }}>Invoice File</th>
                      <th style={{ padding: '8px 12px' }}>Status</th>
                      <th style={{ padding: '8px 12px' }}>Extracted Items</th>
                      <th style={{ padding: '8px 12px' }}>Calculated Ready</th>
                      <th style={{ padding: '8px 12px' }}>Total Footprint</th>
                      <th style={{ padding: '8px 12px' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bulkBatchData.jobs.map((job, idx) => (
                      <tr key={idx} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                        <td style={{ padding: '8px 12px', color: themeSubtext }}>{idx + 1}</td>
                        <td style={{ padding: '8px 12px', fontWeight: '700', color: themeText }}>{job.filename}</td>
                        <td style={{ padding: '8px 12px' }}>
                          <span style={{
                            padding: '3px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: '800',
                            backgroundColor: job.status === 'COMPLETED' ? 'rgba(16,185,129,0.15)' :
                                             job.status === 'REVIEW_REQUIRED' ? 'rgba(234,179,8,0.15)' :
                                             job.status === 'PROCESSING' ? 'rgba(59,130,246,0.15)' :
                                             job.status === 'FAILED' ? 'rgba(239,68,68,0.15)' : 'rgba(148,163,184,0.15)',
                            color: job.status === 'COMPLETED' ? '#10b981' :
                                   job.status === 'REVIEW_REQUIRED' ? '#eab308' :
                                   job.status === 'PROCESSING' ? '#3b82f6' :
                                   job.status === 'FAILED' ? '#ef4444' : '#94a3b8'
                          }}>
                            {job.status}
                          </span>
                        </td>
                        <td style={{ padding: '8px 12px', color: themeText }}>{job.records_extracted_count || 0}</td>
                        <td style={{ padding: '8px 12px', color: '#10b981', fontWeight: '700' }}>{job.calculation_ready_count || 0}</td>
                        <td style={{ padding: '8px 12px', fontWeight: '800', color: job.total_kg_co2e > 0 ? '#10b981' : themeSubtext }}>
                          {job.total_kg_co2e ? `${job.total_kg_co2e.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} kg CO2e` : '—'}
                        </td>
                        <td style={{ padding: '8px 12px' }}>
                          {job.records && job.records.length > 0 && (
                            <button
                              onClick={() => handleInspectJob(job)}
                              style={{
                                padding: '4px 10px', borderRadius: '6px', fontSize: '10px', fontWeight: '700',
                                backgroundColor: isDarkMode ? '#1f2937' : '#e2e8f0', color: themeText,
                                border: 'none', cursor: 'pointer'
                              }}>
                              Inspect Items
                            </button>
                          )}
                          {job.error_message && (
                            <span style={{ color: '#ef4444', fontSize: '10px' }} title={job.error_message}>
                              ⚠️ {job.error_message.slice(0, 30)}...
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* REAL-TIME SINGLE PIPELINE PROGRESS STATE */}
      {universalStatus === 'uploading' && uploadMode === 'single' && (
        <div style={{
          padding: '36px 32px', borderRadius: '18px', backgroundColor: themeCard, border: `1px solid ${themeBorder}`,
          display: 'flex', flexDirection: 'column', gap: '24px', boxShadow: '0 8px 24px rgba(0,0,0,0.15)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{
                width: '42px', height: '42px', borderRadius: '50%',
                border: '3px solid rgba(16,185,129,0.2)', borderTopColor: '#10b981',
                animation: 'spin 1s linear infinite'
              }} />
              <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
              <div>
                <h4 style={{ margin: '0 0 4px 0', color: themeText, fontSize: '16px', fontWeight: '800' }}>
                  Processing {universalFile?.name || 'Document'} in Real-Time
                </h4>
                <p style={{ margin: 0, fontSize: '12px', color: themeSubtext }}>
                  Document AI is executing extraction heuristics and authoritative GHG matching.
                </p>
              </div>
            </div>
            <span style={{ fontSize: '12px', padding: '6px 14px', borderRadius: '20px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', fontWeight: '700' }}>
              Live AI Pipeline Active
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginTop: '10px' }}>
            {[
              { step: '1. Receive & Parse', desc: 'Reading PDF tokens & tables', icon: '📑' },
              { step: '2. Classify & Segment', desc: 'Invoices, Fuels, Freight, Utilities', icon: '🔍' },
              { step: '3. Extract & Normalize', desc: 'Physical quantities & units', icon: '⚡' },
              { step: '4. Validate & Match', desc: 'GHG Protocol & CBAM factors', icon: '🌿' }
            ].map((st, i) => (
              <div key={i} style={{
                padding: '16px', borderRadius: '12px', backgroundColor: isDarkMode ? '#0d131f' : '#f8fafc',
                border: `1px solid ${themeBorder}`, display: 'flex', gap: '10px', alignItems: 'center'
              }}>
                <span style={{ fontSize: '20px' }}>{st.icon}</span>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '700', color: themeText }}>{st.step}</div>
                  <div style={{ fontSize: '11px', color: themeSubtext }}>{st.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ERROR STATE */}
      {universalStatus === 'error' && uploadMode === 'single' && (
        <div style={{
          padding: '24px', borderRadius: '18px', backgroundColor: 'rgba(239,68,68,0.08)',
          border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444'
        }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <span style={{ fontSize: '20px' }}>⚠️</span>
            <div>
              <h4 style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: '800' }}>Extraction Error</h4>
              <p style={{ margin: 0, fontSize: '12px' }}>{errorMessage || 'Unable to extract data from the uploaded file.'}</p>
            </div>
          </div>
        </div>
      )}

      {/* EMPTY RESULT STATE */}
      {universalStatus === 'empty' && uploadMode === 'single' && (
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
      {universalStatus === 'idle' && reviewedRecords.length === 0 && !bulkBatchData && (
        <div style={{
          padding: '48px', borderRadius: '18px', backgroundColor: themeCard, border: `1px dashed ${themeBorder}`,
          textAlign: 'center', color: themeSubtext
        }}>
          <div style={{ fontSize: '36px', marginBottom: '10px' }}>📄</div>
          <h4 style={{ margin: '0 0 6px 0', color: themeText, fontSize: '15px', fontWeight: '700' }}>
            No document uploaded
          </h4>
          <p style={{ margin: 0, fontSize: '12px', maxWidth: '420px', marginInline: 'auto' }}>
            Upload single or bulk PDF documents above to parse line items, review extracted quantities & calculate audited emissions.
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
                Extracted directly via Document AI model without placeholder or fallback values.
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
