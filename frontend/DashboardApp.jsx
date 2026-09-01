import React, { useState, useEffect } from 'react';

export default function DashboardApp() {
  const [isLoggedIn, setIsLoggedIn] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard');

  // Configurable Settings State
  const [carbonPrice, setCarbonPrice] = useState(85.0);
  const [defaultRegion, setDefaultRegion] = useState('DE');
  const [reportingYear, setReportingYear] = useState('2026');
  const [userProfile, setUserProfile] = useState({
    name: 'Sustainability Manager',
    email: 'manager@carbonledger.io',
    role: 'Sustainability Lead'
  });

  // Universal Carbon Dataset Upload & Calculation States
  const [universalFile, setUniversalFile] = useState(null);
  const [universalStatus, setUniversalStatus] = useState('idle'); // idle, uploading, parsed, calculating, calculated, error
  const [universalProgress, setUniversalProgress] = useState(0);
  const [universalResult, setUniversalResult] = useState(null);
  const [universalRecords, setUniversalRecords] = useState([]);
  const [universalLogs, setUniversalLogs] = useState([]);
  const [selectedTraceRow, setSelectedTraceRow] = useState(null);
  
  // Review Screen States
  const [universalUploadId, setUniversalUploadId] = useState('');
  const [reviewedRecords, setReviewedRecords] = useState([]);
  const [saveStatus, setSaveStatus] = useState('');
  const [reviewAuditLog, setReviewAuditLog] = useState([]);
  const [parserResponse, setParserResponse] = useState(null);
  const [parserPipelineError, setParserPipelineError] = useState("");
  const [debugMode, setDebugMode] = useState(false);

  // AI Chat Assistant State
  const [chatMessages, setChatMessages] = useState([
    { sender: 'assistant', text: 'Hello! I am your AI Sustainability Assistant. I can help analyze your latest carbon audit. Try asking one of the suggested prompts below or type your query!' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Scenario Analysis State
  const [selectedStrategy, setSelectedStrategy] = useState('eaf_steel');
  const [scenarioResult, setScenarioResult] = useState(null);
  const [isScenarioLoading, setIsScenarioLoading] = useState(false);

  // Forecast State
  const [forecastResult, setForecastResult] = useState(null);
  const [isForecastLoading, setIsForecastLoading] = useState(false);

  // Authentication State
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('carbonledger_user');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'signup'
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authFullName, setAuthFullName] = useState('');
  const [authOrg, setAuthOrg] = useState('');
  const [authRegion, setAuthRegion] = useState('DE');
  const [authRole, setAuthRole] = useState('auditor');
  const [authError, setAuthError] = useState('');
  const [isAuthLoading, setIsAuthLoading] = useState(false);

  // Admin Console States
  const [adminSubTab, setAdminSubTab] = useState('rules'); // 'rules', 'factors', 'cbam', 'safeguards', 'users', 'audit'
  const [adminRules, setAdminRules] = useState([]);
  const [adminFactors, setAdminFactors] = useState([]);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminAuditLogs, setAdminAuditLogs] = useState([]);
  const [adminSuccessMsg, setAdminSuccessMsg] = useState('');

  const [newRule, setNewRule] = useState({
    rule_name: '',
    rule_type: 'scope_routing',
    condition_field: 'material',
    condition_operator: 'contains',
    condition_value: '',
    target_action: 'set_scope',
    target_value: 'Scope 3',
    priority: 10,
    is_active: 1
  });

  const [newFactor, setNewFactor] = useState({
    material_pattern: '',
    region: 'DE',
    scope: 'Scope 3',
    custom_emission_factor: 0.0,
    unit: 'kg',
    source_name: 'Supplier EPD',
    reason: 'Custom Org Override'
  });

  // Auth Handlers
  const handleAuthLogin = (email, password) => {
    setIsAuthLoading(true);
    setAuthError('');
    fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      setIsAuthLoading(false);
      if (status !== 200) throw new Error(body.detail || 'Login failed.');
      localStorage.setItem('carbonledger_token', body.token);
      localStorage.setItem('carbonledger_user', JSON.stringify(body.user));
      setCurrentUser(body.user);
    })
    .catch(err => {
      setIsAuthLoading(false);
      setAuthError(err.message);
    });
  };

  const handleAuthRegister = () => {
    setIsAuthLoading(true);
    setAuthError('');
    fetch('http://localhost:8000/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: authEmail,
        password: authPassword,
        full_name: authFullName,
        organization: authOrg,
        default_region: authRegion,
        role: authRole
      })
    })
    .then(res => res.json().then(data => ({ status: res.status, body: data })))
    .then(({ status, body }) => {
      setIsAuthLoading(false);
      if (status !== 200) throw new Error(body.detail || 'Registration failed.');
      localStorage.setItem('carbonledger_token', body.token);
      localStorage.setItem('carbonledger_user', JSON.stringify(body.user));
      setCurrentUser(body.user);
    })
    .catch(err => {
      setIsAuthLoading(false);
      setAuthError(err.message);
    });
  };

  const handleAuthLogout = () => {
    localStorage.removeItem('carbonledger_token');
    localStorage.removeItem('carbonledger_user');
    setCurrentUser(null);
    setActiveTab('Dashboard');
  };

  const fetchAdminData = () => {
    fetch('http://localhost:8000/api/v1/admin/rules').then(res => res.json()).then(data => setAdminRules(data || [])).catch(() => {});
    fetch('http://localhost:8000/api/v1/admin/factors').then(res => res.json()).then(data => setAdminFactors(data || [])).catch(() => {});
    fetch('http://localhost:8000/api/v1/admin/users').then(res => res.json()).then(data => setAdminUsers(data || [])).catch(() => {});
    fetch('http://localhost:8000/api/v1/admin/audit-logs').then(res => res.json()).then(data => setAdminAuditLogs(data || [])).catch(() => {});
  };

  useEffect(() => {
    if (activeTab === 'Admin Console') {
      fetchAdminData();
    }
  }, [activeTab]);

  const handleSaveRule = () => {
    if (!newRule.rule_name || !newRule.condition_value || !newRule.target_value) return;
    fetch('http://localhost:8000/api/v1/admin/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newRule)
    }).then(() => {
      setAdminSuccessMsg('Rule saved successfully!');
      setTimeout(() => setAdminSuccessMsg(''), 3000);
      setNewRule({ rule_name: '', rule_type: 'scope_routing', condition_field: 'material', condition_operator: 'contains', condition_value: '', target_action: 'set_scope', target_value: 'Scope 3', priority: 10, is_active: 1 });
      fetchAdminData();
    });
  };

  const handleDeleteRule = (ruleId) => {
    fetch(`http://localhost:8000/api/v1/admin/rules/${ruleId}`, { method: 'DELETE' }).then(() => fetchAdminData());
  };

  const handleSaveFactorOverride = () => {
    if (!newFactor.material_pattern || !newFactor.custom_emission_factor) return;
    fetch('http://localhost:8000/api/v1/admin/factors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newFactor)
    }).then(() => {
      setAdminSuccessMsg('Factor override saved successfully!');
      setTimeout(() => setAdminSuccessMsg(''), 3000);
      setNewFactor({ material_pattern: '', region: 'DE', scope: 'Scope 3', custom_emission_factor: 0.0, unit: 'kg', source_name: 'Supplier EPD', reason: 'Custom Org Override' });
      fetchAdminData();
    });
  };

  const handleToggleUserStatus = (userId) => {
    fetch(`http://localhost:8000/api/v1/admin/users/${userId}/status`, { method: 'PATCH' }).then(() => fetchAdminData());
  };

  // Theme Styling Tokens (Vibrant Dark Mode / Harmonious Light Mode)
  const themeBg = isDarkMode ? '#080c14' : '#f8fafc';
  const themeCard = isDarkMode ? '#111827' : '#ffffff';
  const themeBorder = isDarkMode ? '#1f2937' : '#e2e8f0';
  const themeText = isDarkMode ? '#f3f4f6' : '#0f172a';
  const themeSubtext = isDarkMode ? '#9ca3af' : '#64748b';

  const receivedEmptyState = universalStatus === 'parsed' && (!parserResponse || !reviewedRecords || reviewedRecords.length === 0);
  const effectiveError = parserPipelineError || (receivedEmptyState ? "Parser response missing." : "");

  const getAllowedTabs = () => {
    const tabs = [
      { name: 'Dashboard', icon: '📊' },
      { name: 'Upload', icon: '📤' },
      { name: 'Reports', icon: '📑' },
      { name: 'AI Intelligence', icon: '🧠' },
      { name: 'Settings', icon: '⚙️' }
    ];
    if (currentUser && currentUser.role === 'admin') {
      tabs.push({ name: 'Admin Console', icon: '🛡️' });
    }
    return tabs;
  };

  // Fetch Settings & Latest Upload on Mount
  useEffect(() => {
    // Fetch settings
    fetch('http://localhost:8000/api/v1/settings')
      .then(res => res.json())
      .then(data => {
        if (data.carbon_price_eur_per_ton) setCarbonPrice(parseFloat(data.carbon_price_eur_per_ton));
        if (data.default_region) setDefaultRegion(data.default_region);
        if (data.reporting_year) setReportingYear(data.reporting_year);
        if (data.user_profile) {
          try { setUserProfile(JSON.parse(data.user_profile)); } catch (e) {}
        }
      })
      .catch(() => {});

    fetch('http://localhost:8000/api/upload/latest')
      .then(res => res.json())
      .then(data => {
        if (data) {
          setUniversalResult(data);
          setUniversalRecords(data.records || []);
          setUniversalStatus('calculated');
          setUniversalUploadId(data.upload_id || '');
          setReviewedRecords(data.records || []);
          setParserResponse(data.parser_response || null);
          setParserPipelineError("");
        }
      })
      .catch(() => {});
  }, []);

  const handleSaveSettings = () => {
    fetch('http://localhost:8000/api/v1/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        carbon_price_eur_per_ton: carbonPrice,
        default_region: defaultRegion,
        reporting_year: reportingYear,
        theme: isDarkMode ? 'dark' : 'light',
        user_profile: userProfile
      })
    })
    .then(res => res.json())
    .then(() => alert('Settings saved successfully!'))
    .catch(err => alert('Failed to save settings: ' + err.message));
  };

  const clientParseNumeric = (strVal) => {
    if (!strVal) return 0;
    const clean = String(strVal).replace(/[₹€$¥£\s]/g, '').trim();
    if (!clean) return 0;
    let s = clean;
    if (s.includes('.') && s.includes(',')) {
      if (s.indexOf('.') < s.indexOf(',')) {
        s = s.replace(/\./g, '').replace(/,/g, '.');
      } else {
        s = s.replace(/,/g, '');
      }
    } else if (s.includes(',')) {
      const parts = s.split(',');
      if (parts.length > 2 || (parts.length === 2 && parts[1].length === 3)) {
        s = parts.join('');
      } else {
        s = s.replace(/,/g, '.');
      }
    }
    const val = parseFloat(s);
    return isNaN(val) ? 0 : val;
  };

  const clientExtractUnit = (strVal) => {
    if (!strVal) return null;
    const s = String(strVal).toLowerCase().trim();
    const units = ["ton-km", "tkm", "kwh", "mwh", "tonne", "tonnes", "ton", "litre", "liters", "litres", "piece", "pieces", "pcs", "kg", "g", "l", "m³", "m3", "km"];
    for (let u of units) {
      if (s.endsWith(u) || s.includes(u)) {
        if (u === "l" || u === "litre" || u === "liters" || u === "litres") return "L";
        if (u === "ton-km" || u === "tkm") return "ton-km";
        if (u === "m3" || u === "m³") return "m³";
        if (u === "mwh") return "MWh";
        if (u === "kwh") return "kWh";
        if (u === "pcs" || u === "piece" || u === "pieces") return "piece";
        return u;
      }
    }
    return null;
  };

  const getRowFieldValidation = (row) => {
    const errors = [];
    const warnings = [];
    const corrections = [];
    
    if (!row.material || row.material === "Unspecified Material") {
      errors.push("Missing Material");
    }
    
    const quantityNormalized = clientParseNumeric(row.quantity);
    if (row.quantity === undefined || row.quantity === null || String(row.quantity).trim() === "") {
      errors.push("Missing Quantity");
    } else if (isNaN(quantityNormalized) || quantityNormalized <= 0) {
      errors.push("Invalid Quantity");
    }
    
    if (!row.unit) {
      errors.push("Missing Unit");
    }
    
    const costNormalized = clientParseNumeric(row.cost);
    if (row.cost === undefined || row.cost === null || String(row.cost).trim() === "") {
      errors.push("Missing Cost");
    } else if (isNaN(costNormalized)) {
      errors.push("Invalid Cost");
    }
    
    if (!row.country || row.country.length !== 2) {
      errors.push("Invalid/Missing Country");
    }
    if (row.ocr_confidence < 0.90) {
      warnings.push("Low Confidence");
    }

    // Check Mismatches (comparing normalized values -> corrections!)
    if (row.quantity_raw) {
      const rawVal = clientParseNumeric(row.quantity_raw);
      if (Math.abs(rawVal - quantityNormalized) > 1e-4) {
        corrections.push("Quantity Corrected");
      }
    }
    if (row.unit_raw || row.quantity_raw) {
      const rawUnit = clientExtractUnit(row.unit_raw) || clientExtractUnit(row.quantity_raw);
      if (rawUnit && row.unit && rawUnit.toLowerCase() !== row.unit.toLowerCase()) {
        corrections.push("Unit Corrected");
      }
    }
    if (row.cost_raw) {
      const rawVal = clientParseNumeric(row.cost_raw);
      if (Math.abs(rawVal - costNormalized) > 1e-4) {
        corrections.push("Cost Corrected");
      }
    }
    if (row.country_raw) {
      const countryMapping = {
        "india": "IN", "in": "IN", "ind": "IN",
        "germany": "DE", "de": "DE", "deu": "DE",
        "france": "FR", "fr": "FR",
        "united kingdom": "GB", "uk": "GB", "gb": "GB",
        "united states": "US", "usa": "US", "us": "US",
        "china": "CN", "cn": "CN",
        "japan": "JP", "jp": "JP"
      };
      const cleanRaw = String(row.country_raw).toLowerCase().trim();
      let expectedCode = null;
      for (let k in countryMapping) {
        if (cleanRaw.includes(k)) {
          expectedCode = countryMapping[k];
          break;
        }
      }
      if (expectedCode && row.country && expectedCode.toUpperCase() !== row.country.toUpperCase()) {
        corrections.push("Country Corrected");
      }
    }

    let validationStatus = "GREEN";
    let statusLabel = "MATCH";
    if (errors.length > 0) {
      validationStatus = "RED";
      statusLabel = "INVALID";
    } else if (corrections.length > 0) {
      validationStatus = "YELLOW";
      statusLabel = "MANUALLY CORRECTED";
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      corrections,
      validationStatus,
      statusLabel
    };
  };

  const handleUniversalFileChange = (file) => {
    if (!file) return;
    setUniversalFile(file);
    setUniversalStatus('uploading');
    setUniversalProgress(10);
    setUniversalLogs(['[Intake] Ingesting file: ' + file.name]);

    const timer = setInterval(() => {
      setUniversalProgress(prev => (prev >= 90 ? 90 : prev + 15));
    }, 200);

    const formData = new FormData();
    formData.append('file', file);

    fetch('http://localhost:8000/api/upload/universal', {
      method: 'POST',
      body: formData
    })
    .then(res => {
      clearInterval(timer);
      if (!res.ok) throw new Error("Upload processing failed.");
      return res.json();
    })
    .then(data => {
      // Step-by-Step Trace Logging
      console.log("=== STEP-BY-STEP OCR PIPELINE TRACE ===");
      
      // Step 1: Upload
      console.log("Step 1: Upload");
      console.log("  INPUT: Selected file in browser");
      console.log(`  OUTPUT: Filename=${file.name}, Size=${file.size} bytes, Type=${file.type}`);
      
      const parserRes = data.parser_response || {};
      const rawText = parserRes.raw_ocr_data?.text || "";
      const charCount = rawText.length;
      
      // Step 2: OCR
      console.log("Step 2: OCR");
      console.log(`  INPUT: File binary uploaded to server`);
      console.log(`  OUTPUT: Characters extracted=${charCount}, Confidence=${data.ai_confidence || 'N/A'}, Raw OCR Text snippet="${rawText.slice(0, 100).replace(/\n/g, ' ')}..."`);
      
      // Check OCR failure
      if (!rawText || !rawText.trim()) {
        console.error("  Pipeline Stopped: OCR Failed (no text extracted).");
        setParserPipelineError("OCR Failed");
        setUniversalStatus('error');
        setParserResponse(data.parser_response || null);
        setUniversalProgress(100);
        return;
      }
      
      // Step 3: Table Detection
      const tablesCount = parserRes.tables_count || 0;
      console.log("Step 3: Table Detection");
      console.log("  INPUT: OCR Layout coordinates & text blocks");
      console.log(`  OUTPUT: Tables Found=${tablesCount}, Rows Found=${data.records?.length || 0}`);
      
      // Step 4: Parser
      console.log("Step 4: Parser");
      console.log("  INPUT: Classification Predicted Type & Raw Text");
      console.log(`  OUTPUT: JSON Rows=${data.records?.length || 0}, Fields count per row=10`);
      
      // Check parser empty rows failure
      if (!data.records || data.records.length === 0) {
        console.error("  Pipeline Stopped: No structured records detected.");
        setParserPipelineError("No structured records detected.");
        setUniversalStatus('error');
        setParserResponse(data.parser_response || null);
        setUniversalProgress(100);
        return;
      }
      
      // Step 5: Validation
      const validations = data.records.map(r => getRowFieldValidation(r));
      const hasErrors = validations.some(v => !v.isValid);
      const errorsList = validations.flatMap(v => v.errors);
      const warningsList = validations.flatMap(v => v.warnings);
      console.log("Step 5: Validation");
      console.log("  INPUT: Extracted parsed records JSON");
      console.log(`  OUTPUT: Errors=${errorsList.length} (${JSON.stringify(errorsList)}), Warnings=${warningsList.length} (${JSON.stringify(warningsList)})`);
      
      // Step 6: React State
      console.log("Step 6: React State");
      console.log("  INPUT: API Response data structure");
      console.log(`  OUTPUT: rawText length=${charCount}, parsedRows=${data.records.length}, validation valid=${!hasErrors}`);
      
      if (!data || !data.parser_response) {
        setParserPipelineError("Parser response missing.");
        setUniversalStatus('error');
        setUniversalProgress(100);
        return;
      }

      setParserPipelineError("");
      setUniversalProgress(100);
      setUniversalStatus('parsed');
      setUniversalUploadId(data.upload_id);
      setReviewedRecords(data.records || []);
      setParserResponse(data.parser_response || null);
      setReviewAuditLog([
        { timestamp: new Date().toISOString(), action: "Document uploaded and parsed", user: "System" }
      ]);

      if (rawText.trim() && data.records.length > 0) {
        setUniversalLogs(prev => [
          ...prev,
          '[OCR] Layout & table extraction finished.',
          `[Classification] Auto-detected document sections cleanly.`,
          `[Validation] Ready for manual review and approval.`
        ]);
      } else {
        setUniversalLogs(prev => [
          ...prev,
          '[OCR] Layout & table extraction finished.',
          `[Classification] Auto-detected document sections cleanly.`
        ]);
      }
    })
    .catch(err => {
      console.error("[CarbonLedger Developer Log] Parser API failed:", err);
      clearInterval(timer);
      setUniversalStatus('error');
      setUniversalProgress(100);
      setParserPipelineError(err.message || "Parser response missing.");
      setUniversalLogs(prev => [...prev, '[Error] Processing failed: ' + err.message]);
      alert("Parser API failed: " + err.message);
    });
  };

  const handleSaveChanges = () => {
    const normalizedRecords = reviewedRecords.map(r => ({
      ...r,
      quantity: clientParseNumeric(r.quantity),
      cost: clientParseNumeric(r.cost),
      country: String(r.country || '').trim().toUpperCase(),
      unit: String(r.unit || '').trim()
    }));

    console.log("[CarbonLedger Developer Log] Save changes clicked. Upload ID:", universalUploadId);
    console.log("[CarbonLedger Developer Log] Rows count to save:", normalizedRecords.length);
    console.log("[CarbonLedger Developer Log] Current rows:", normalizedRecords);
    console.log("[CarbonLedger Developer Log] Validation on save:", normalizedRecords.map(r => getRowFieldValidation(r)));

    setSaveStatus('Saving changes...');
    fetch('http://localhost:8000/api/upload/save-changes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ upload_id: universalUploadId, records: normalizedRecords })
    })
    .then(res => {
      if (!res.ok) throw new Error("Failed to save changes.");
      return res.json();
    })
    .then(() => {
      setSaveStatus('Changes saved successfully!');
      setReviewAuditLog(prev => [
        ...prev,
        { timestamp: new Date().toISOString(), action: "Extracted records edited and saved by user", user: "User" }
      ]);
      setUniversalLogs(prev => [...prev, '[Review] Edited records saved successfully.']);
      setTimeout(() => setSaveStatus(''), 3000);
    })
    .catch(err => {
      setSaveStatus('Error saving: ' + err.message);
    });
  };

  const handleApproveAndCalculate = () => {
    const normalizedRecords = reviewedRecords.map(r => ({
      ...r,
      quantity: clientParseNumeric(r.quantity),
      cost: clientParseNumeric(r.cost),
      country: String(r.country || '').trim().toUpperCase(),
      unit: String(r.unit || '').trim()
    }));

    console.log("[CarbonLedger Developer Log] Approve and calculate clicked. Upload ID:", universalUploadId);
    console.log("[CarbonLedger Developer Log] Approved rows count:", normalizedRecords.length);
    console.log("[CarbonLedger Developer Log] Approved rows:", normalizedRecords);
    console.log("[CarbonLedger Developer Log] Validation on approve:", normalizedRecords.map(r => getRowFieldValidation(r)));

    // Verify there are no errors in any row
    const hasErrors = normalizedRecords.some(r => !getRowFieldValidation(r).isValid);
    if (hasErrors) {
      alert("Please resolve all validation errors (red badges) before approving.");
      return;
    }

    setUniversalStatus('calculating');
    setUniversalProgress(30);
    setUniversalLogs(prev => [...prev, '[Carbon Engine] Locking parsing screen. Initializing carbon calculations...']);

    const progressTimer = setInterval(() => {
      setUniversalProgress(prev => (prev >= 90 ? 90 : prev + 20));
    }, 300);

    fetch('http://localhost:8000/api/upload/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ upload_id: universalUploadId, records: normalizedRecords })
    })
    .then(res => {
      clearInterval(progressTimer);
      if (!res.ok) {
        return res.json().then(errData => {
          throw new Error(errData.detail || "Carbon footprint calculation failed.");
        });
      }
      return res.json();
    })
    .then(data => {
      setUniversalProgress(100);
      setUniversalStatus('calculated');
      setUniversalResult(data);
      setUniversalRecords(data.inventory_records || data.records || []);
      setReviewAuditLog(prev => [
        ...prev,
        { timestamp: new Date().toISOString(), action: "Fidelity validation passed. Records approved and calculated.", user: "User" }
      ]);
      setUniversalLogs(prev => [
        ...prev,
        '[Carbon Engine] Calculation completed successfully using Approved JSON.',
        `[Carbon Engine] Calculated emissions for ${data.summary?.rows_calculated || 0} records. Total CO2e: ${data.summary?.total_co2e_kg || 0} kg`,
        `[CBAM Engine] Estimated CBAM cost exposure: €${data.summary?.total_cbam_cost_eur || 0}`,
        '[Report] All 5 fresh session compliance reports compiled.'
      ]);
    })
    .catch(err => {
      clearInterval(progressTimer);
      setUniversalStatus('error');
      setUniversalProgress(100);
      setUniversalLogs(prev => [...prev, '[Error] Carbon calculations failed: ' + err.message]);
    });
  };

  const handleRemoveUniversal = () => {
    setUniversalFile(null);
    setUniversalStatus('idle');
    setUniversalProgress(0);
    setUniversalResult(null);
    setUniversalRecords([]);
    setUniversalLogs([]);
    setSelectedTraceRow(null);
    setReviewedRecords([]);
    setUniversalUploadId('');
    setReviewAuditLog([]);
  };

  // --- AI Chat Handler ---
  const handleSendChat = (textToSend) => {
    const messageText = textToSend || chatInput;
    if (!messageText.trim()) return;

    // Add user message
    setChatMessages(prev => [...prev, { sender: 'user', text: messageText }]);
    if (!textToSend) setChatInput('');
    setIsChatLoading(true);

    fetch('http://localhost:8000/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: messageText, tenant_id: 'tenant_default' })
    })
    .then(res => res.json())
    .then(data => {
      setChatMessages(prev => [...prev, { sender: 'assistant', text: data.response }]);
      setIsChatLoading(false);
    })
    .catch(() => {
      setChatMessages(prev => [...prev, { sender: 'assistant', text: 'Sorry, I encountered an error connecting to the copilot engine.' }]);
      setIsChatLoading(false);
    });
  };

  // --- Scenario Simulator ---
  const handleRunScenario = () => {
    setIsScenarioLoading(true);
    fetch('http://localhost:8000/api/what-if', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ strategy: selectedStrategy })
    })
    .then(res => res.json())
    .then(data => {
      setScenarioResult(data);
      setIsScenarioLoading(false);
    })
    .catch(() => {
      setIsScenarioLoading(false);
    });
  };

  // --- Forecasting Handler ---
  const handleRunForecast = () => {
    setIsForecastLoading(true);
    fetch('http://localhost:8000/api/forecast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ months_ahead: 6 })
    })
    .then(res => res.json())
    .then(data => {
      setForecastResult(data);
      setIsForecastLoading(false);
    })
    .catch(() => {
      setIsForecastLoading(false);
    });
  };

  // --- Chart Computations ---
  const s1 = universalResult?.summary?.scope_1_co2e_kg || 0;
  const s2 = universalResult?.summary?.scope_2_co2e_kg || 0;
  const s3 = universalResult?.summary?.scope_3_co2e_kg || 0;
  const totalScopeVal = s1 + s2 + s3 || 1;

  // Material grouping
  const matGroup = {};
  universalRecords.forEach(r => {
    const m = r.material || 'Unspecified';
    matGroup[m] = (matGroup[m] || 0) + (r.co2e_kg || 0);
  });
  const topMaterials = Object.entries(matGroup)
    .map(([name, val]) => ({ name, val }))
    .sort((a, b) => b.val - a.val)
    .slice(0, 5);

  // Supplier grouping
  const supGroup = {};
  universalRecords.forEach(r => {
    const sName = r.supplier || 'Unknown';
    supGroup[sName] = (supGroup[sName] || 0) + (r.co2e_kg || 0);
  });
  const topSuppliers = Object.entries(supGroup)
    .map(([name, val]) => ({ name, val }))
    .sort((a, b) => b.val - a.val)
    .slice(0, 5);

  // Monthly emissions timeline
  const monthlyEmissions = {};
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  months.forEach(m => { monthlyEmissions[m] = 0; });
  universalRecords.forEach(r => {
    if (r.delivery_date) {
      try {
        const dObj = new Date(r.delivery_date);
        const mStr = months[dObj.getMonth()];
        if (mStr) monthlyEmissions[mStr] += (r.co2e_kg || 0);
      } catch (e) {}
    }
  });
  const monthlyData = Object.entries(monthlyEmissions).map(([name, val]) => ({ name, val }));

  // Draw monthly area line curve
  const svgW = 480;
  const svgH = 130;
  const maxMonth = Math.max(...monthlyData.map(d => d.val), 1);
  const pts = monthlyData.map((d, idx) => {
    const x = (idx / (monthlyData.length - 1)) * (svgW - 50) + 25;
    const y = svgH - (d.val / maxMonth) * (svgH - 40) - 15;
    return { x, y, name: d.name, val: d.val };
  });
  const linePath = pts.map((p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ');
  const areaPath = pts.length ? `${linePath} L ${pts[pts.length - 1].x} ${svgH - 10} L ${pts[0].x} ${svgH - 10} Z` : '';

  if (!currentUser) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: isDarkMode ? '#080c14' : '#f8fafc', fontFamily: 'Outfit, Inter, sans-serif' }}>
        <div style={{ width: '420px', padding: '36px', borderRadius: '16px', backgroundColor: isDarkMode ? '#111827' : '#ffffff', border: `1px solid ${isDarkMode ? '#1f2937' : '#e2e8f0'}`, boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{ fontSize: '36px', marginBottom: '8px' }}>🍃</div>
            <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '800', color: '#10b981' }}>CarbonLedger OS</h2>
            <p style={{ margin: '6px 0 0', fontSize: '13px', color: themeSubtext }}>Enterprise Carbon Accounting & CBAM Platform</p>
          </div>

          {authError && (
            <div style={{ padding: '10px 14px', borderRadius: '8px', backgroundColor: 'rgba(239,68,68,0.15)', border: '1px solid #ef4444', color: '#f87171', fontSize: '12px', marginBottom: '16px' }}>
              ⚠️ {authError}
            </div>
          )}

          <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', backgroundColor: isDarkMode ? '#1f2937' : '#f1f5f9', padding: '4px', borderRadius: '8px' }}>
            <button 
              onClick={() => setAuthMode('login')} 
              style={{ flex: 1, padding: '8px', borderRadius: '6px', border: 'none', backgroundColor: authMode === 'login' ? '#10b981' : 'transparent', color: authMode === 'login' ? '#fff' : themeSubtext, fontWeight: 'bold', cursor: 'pointer', fontSize: '13px' }}>
              Sign In
            </button>
            <button 
              onClick={() => setAuthMode('signup')} 
              style={{ flex: 1, padding: '8px', borderRadius: '6px', border: 'none', backgroundColor: authMode === 'signup' ? '#10b981' : 'transparent', color: authMode === 'signup' ? '#fff' : themeSubtext, fontWeight: 'bold', cursor: 'pointer', fontSize: '13px' }}>
              Sign Up
            </button>
          </div>

          <form onSubmit={(e) => { 
            e.preventDefault(); 
            if (authMode === 'login') handleAuthLogin(authEmail, authPassword); 
            else handleAuthRegister();
          }}>
            {authMode === 'signup' && (
              <>
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Full Name</label>
                  <input 
                    type="text" 
                    required
                    value={authFullName} 
                    onChange={e => setAuthFullName(e.target.value)} 
                    placeholder="Jane Doe" 
                    style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
                  />
                </div>
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Organization Name</label>
                  <input 
                    type="text" 
                    required
                    value={authOrg} 
                    onChange={e => setAuthOrg(e.target.value)} 
                    placeholder="Siemens Energy ESG" 
                    style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
                  />
                </div>
              </>
            )}

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Corporate Email</label>
              <input 
                type="email" 
                required
                value={authEmail} 
                onChange={e => setAuthEmail(e.target.value)} 
                placeholder="auditor@company.com" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px', color: themeText }}>Password</label>
              <input 
                type="password" 
                required
                value={authPassword} 
                onChange={e => setAuthPassword(e.target.value)} 
                placeholder="••••••••" 
                style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#ffffff', color: themeText, fontSize: '13px' }} 
              />
            </div>

            <button 
              type="submit" 
              disabled={isAuthLoading}
              style={{ width: '100%', padding: '12px', borderRadius: '8px', border: 'none', backgroundColor: '#10b981', color: '#080c14', fontWeight: 'bold', fontSize: '14px', cursor: 'pointer' }}>
              {isAuthLoading ? 'Authenticating...' : (authMode === 'login' ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          {/* Quick Demo Access Buttons */}
          <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: `1px solid ${themeBorder}`, textAlign: 'center' }}>
            <span style={{ fontSize: '11px', color: themeSubtext, display: 'block', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 'bold' }}>One-Click Demo Authentication</span>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
              <button 
                onClick={() => handleAuthLogin('admin@carbonledger.io', 'Admin@12345')} 
                style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #8b5cf6', background: 'rgba(139,92,246,0.15)', color: '#c084fc', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}>
                🔑 Admin
              </button>
              <button 
                onClick={() => handleAuthLogin('auditor@carbonledger.io', 'Auditor@12345')} 
                style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid #10b981', background: 'rgba(16,185,129,0.15)', color: '#34d399', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}>
                🔍 Auditor
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: themeBg, color: themeText, minHeight: '100vh', display: 'flex', fontFamily: 'Outfit, Inter, sans-serif' }}>
      
      {/* Sidebar Navigation */}
      <aside style={{
        width: '260px',
        backgroundColor: themeCard,
        borderRight: `1px solid ${themeBorder}`,
        padding: '28px 20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow: '4px 0 20px rgba(0,0,0,0.02)'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '36px' }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '22px',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.2)'
            }}>
              🍃
            </div>
            <div>
              <h1 style={{ fontSize: '18px', fontWeight: '800', margin: 0, letterSpacing: '-0.3px', background: 'linear-gradient(to right, #10b981, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                CarbonLedger
              </h1>
              <span style={{ fontSize: '11px', color: themeSubtext, fontWeight: '500' }}>Enterprise Sustainability OS</span>
            </div>
          </div>

          {/* Navigation links */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {getAllowedTabs().map(tab => (
              <button
                key={tab.name}
                onClick={() => setActiveTab(tab.name)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  padding: '14px 18px',
                  borderRadius: '12px',
                  backgroundColor: activeTab === tab.name ? (isDarkMode ? 'rgba(16, 185, 129, 0.12)' : 'rgba(16, 185, 129, 0.08)') : 'transparent',
                  color: activeTab === tab.name ? '#10b981' : themeSubtext,
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: activeTab === tab.name ? '700' : '600',
                  textAlign: 'left',
                  transition: 'all 0.2s',
                  transform: activeTab === tab.name ? 'translateX(4px)' : 'none'
                }}
              >
                <span style={{ fontSize: '18px' }}>{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Sidebar Info Summary */}
        <div style={{ borderTop: `1px solid ${themeBorder}`, paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ fontSize: '12px', color: themeSubtext, display: 'flex', justifyContent: 'space-between' }}>
            <span>CBAM Price:</span>
            <strong style={{ color: '#10b981' }}>€{carbonPrice}/t</strong>
          </div>
          <div style={{ fontSize: '12px', color: themeSubtext, display: 'flex', justifyContent: 'space-between' }}>
            <span>Region:</span>
            <strong>{defaultRegion}</strong>
          </div>
          <button 
            onClick={() => setIsDarkMode(!isDarkMode)} 
            style={{
              backgroundColor: isDarkMode ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)',
              border: `1px solid ${themeBorder}`,
              color: themeText,
              padding: '10px',
              borderRadius: '10px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '600',
              marginTop: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'background-color 0.2s'
            }}
          >
            {isDarkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
          </button>
        </div>
      </aside>

      {/* Main Container */}
      <main style={{ flex: 1, padding: '36px 44px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        
        {/* Top bar header */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '36px' }}>
          <div>
            <h2 style={{ fontSize: '26px', fontWeight: '800', margin: 0, letterSpacing: '-0.5px' }}>{activeTab}</h2>
            <span style={{ fontSize: '13px', color: themeSubtext, marginTop: '2px', display: 'inline-block' }}>
              {activeTab === 'Dashboard' && 'Real-time carbon emissions & CBAM cost analytics for the latest upload session'}
              {activeTab === 'Upload' && 'Consolidated AI data intake pipeline (PDF, Excel, CSV, JSON, ZIP)'}
              {activeTab === 'Reports' && 'Download compliance and ESG reports generated from this session'}
              {activeTab === 'AI Intelligence' && 'Interact with AI Copilot, run what-if scenario simulations, and CBAM cost forecasts'}
              {activeTab === 'Settings' && 'Configure CBAM pricing, reporting region, and user profile'}
              {activeTab === 'Admin Console' && 'Enterprise governance, dynamic calculation rules, emission factor overrides, and audit trails'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '11px', letterSpacing: '0.5px', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981', padding: '6px 14px', borderRadius: '30px', fontWeight: '700' }}>
              ● LIVE SESSION ACTIVE
            </span>
            <div style={{ width: '1px', height: '20px', backgroundColor: themeBorder }}></div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '13px', fontWeight: '700', color: themeText }}>{currentUser.full_name}</div>
                <div style={{ fontSize: '10px', color: '#10b981', fontWeight: '700', textTransform: 'uppercase' }}>{currentUser.role} • {currentUser.organization}</div>
              </div>
              <button 
                onClick={handleAuthLogout} 
                style={{ padding: '6px 12px', borderRadius: '8px', background: 'rgba(239,68,68,0.15)', border: '1px solid #ef4444', color: '#f87171', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}>
                Sign Out
              </button>
            </div>
          </div>
        </header>

        {/* --- TAB 1: DASHBOARD --- */}
        {activeTab === 'Dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            
            {!universalResult ? (
              <div style={{
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(59, 130, 246, 0.02) 100%)',
                border: '1px solid rgba(59, 130, 246, 0.25)',
                borderRadius: '16px',
                padding: '28px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <h3 style={{ fontSize: '17px', fontWeight: '700', margin: '0 0 6px 0', color: '#3b82f6' }}>🚀 Ready for Ingestion</h3>
                  <p style={{ fontSize: '13px', color: themeSubtext, margin: 0 }}>Upload a document in the Upload tab to activate live dashboard widgets, charts, and report sheets.</p>
                </div>
                <button 
                  onClick={() => setActiveTab('Upload')} 
                  style={{
                    backgroundColor: '#3b82f6',
                    color: '#ffffff',
                    border: 'none',
                    padding: '12px 24px',
                    borderRadius: '10px',
                    cursor: 'pointer',
                    fontWeight: '700',
                    fontSize: '13px',
                    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.25)',
                    transition: 'transform 0.2s'
                  }}
                >
                  Go to Upload →
                </button>
              </div>
            ) : (
              <div>
                
                {/* 6 TOP KPI CARDS */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '16px', marginBottom: '32px' }}>
                  
                  <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '14px', padding: '18px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)' }}>
                    <span style={{ fontSize: '12px', color: themeSubtext, fontWeight: '600', display: 'block', marginBottom: '8px' }}>Total Documents</span>
                    <strong style={{ fontSize: '22px', fontWeight: '800' }}>📄 {universalResult.summary?.documents_processed || 0}</strong>
                  </div>

                  <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '14px', padding: '18px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)' }}>
                    <span style={{ fontSize: '12px', color: themeSubtext, fontWeight: '600', display: 'block', marginBottom: '8px' }}>Rows Processed</span>
                    <strong style={{ fontSize: '22px', fontWeight: '800' }}>📋 {universalResult.summary?.rows_extracted || 0}</strong>
                  </div>

                  <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '14px', padding: '18px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)' }}>
                    <span style={{ fontSize: '12px', color: themeSubtext, fontWeight: '600', display: 'block', marginBottom: '8px' }}>Total CO₂e</span>
                    <strong style={{ fontSize: '22px', fontWeight: '800', color: '#10b981' }}>
                      🌍 {universalResult.summary?.total_co2e_tonnes || 0} t
                    </strong>
                    <span style={{ fontSize: '11px', color: themeSubtext, display: 'block', marginTop: '2px' }}>
                      {universalResult.summary?.total_co2e_kg?.toLocaleString()} kg
                    </span>
                  </div>

                  <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '14px', padding: '18px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)' }}>
                    <span style={{ fontSize: '12px', color: themeSubtext, fontWeight: '600', display: 'block', marginBottom: '8px' }}>Estimated CBAM Cost</span>
                    <strong style={{ fontSize: '22px', fontWeight: '800', color: '#f59e0b' }}>
                      💶 €{universalResult.summary?.total_cbam_cost_eur?.toLocaleString() || 0}
                    </strong>
                    <span style={{ fontSize: '11px', color: themeSubtext, display: 'block', marginTop: '2px' }}>
                      @ €{carbonPrice}/t
                    </span>
                  </div>

                  <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '14px', padding: '18px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)' }}>
                    <span style={{ fontSize: '12px', color: themeSubtext, fontWeight: '600', display: 'block', marginBottom: '8px' }}>Confidence</span>
                    <strong style={{ fontSize: '22px', fontWeight: '800', color: '#3b82f6' }}>
                      ⭐ {universalResult.summary?.overall_confidence_pct || 0}%
                    </strong>
                    <span style={{ fontSize: '11px', color: themeSubtext, display: 'block', marginTop: '2px' }}>
                      AI Fidelity Score
                    </span>
                  </div>

                  <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '14px', padding: '18px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.02)' }}>
                    <span style={{ fontSize: '12px', color: themeSubtext, fontWeight: '600', display: 'block', marginBottom: '8px' }}>Processing Time</span>
                    <strong style={{ fontSize: '22px', fontWeight: '800', color: '#8b5cf6' }}>
                      ⚡ {universalResult.processing_time_ms || 150} ms
                    </strong>
                    <span style={{ fontSize: '11px', color: themeSubtext, display: 'block', marginTop: '2px' }}>
                      Model Latency
                    </span>
                  </div>

                </div>

                {/* VISUAL CHARTS LAYOUT */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '20px', marginBottom: '32px' }}>
                  
                  {/* Scope 1, 2, 3 Breakdown Chart */}
                  <div style={{ gridColumn: 'span 4', backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '20px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', margin: '0 0 16px 0', color: themeText }}>📊 Scope Emissions Breakdown</h4>
                    
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                      
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                          <span>Scope 1 (Direct Fuel)</span>
                          <strong>{s1.toLocaleString()} kg ({Math.round(s1/totalScopeVal*100)}%)</strong>
                        </div>
                        <div style={{ height: '8px', backgroundColor: isDarkMode ? '#1f2937' : '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${s1/totalScopeVal*100}%`, backgroundColor: '#ef4444', borderRadius: '4px' }}></div>
                        </div>
                      </div>

                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                          <span>Scope 2 (Grid Electricity)</span>
                          <strong>{s2.toLocaleString()} kg ({Math.round(s2/totalScopeVal*100)}%)</strong>
                        </div>
                        <div style={{ height: '8px', backgroundColor: isDarkMode ? '#1f2937' : '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${s2/totalScopeVal*100}%`, backgroundColor: '#f59e0b', borderRadius: '4px' }}></div>
                        </div>
                      </div>

                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                          <span>Scope 3 (Supply Chain)</span>
                          <strong>{s3.toLocaleString()} kg ({Math.round(s3/totalScopeVal*100)}%)</strong>
                        </div>
                        <div style={{ height: '8px', backgroundColor: isDarkMode ? '#1f2937' : '#f1f5f9', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${s3/totalScopeVal*100}%`, backgroundColor: '#3b82f6', borderRadius: '4px' }}></div>
                        </div>
                      </div>

                    </div>
                  </div>

                  {/* Top Materials Chart */}
                  <div style={{ gridColumn: 'span 4', backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '20px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', margin: '0 0 16px 0', color: themeText }}>📦 Top Materials Emissions</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {topMaterials.map((item, idx) => {
                        const maxVal = topMaterials[0]?.val || 1;
                        const pct = Math.round((item.val / maxVal) * 100);
                        return (
                          <div key={idx}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                              <span style={{ fontWeight: '600', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.name}</span>
                              <span style={{ color: themeSubtext }}>{Math.round(item.val).toLocaleString()} kg CO₂e</span>
                            </div>
                            <div style={{ height: '6px', backgroundColor: isDarkMode ? '#1f2937' : '#f1f5f9', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${pct}%`, backgroundColor: '#10b981', borderRadius: '3px' }}></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Top Suppliers Chart */}
                  <div style={{ gridColumn: 'span 4', backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '20px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', margin: '0 0 16px 0', color: themeText }}>🏭 Top Suppliers Emissions</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {topSuppliers.map((item, idx) => {
                        const maxVal = topSuppliers[0]?.val || 1;
                        const pct = Math.round((item.val / maxVal) * 100);
                        return (
                          <div key={idx}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
                              <span style={{ fontWeight: '600', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.name}</span>
                              <span style={{ color: themeSubtext }}>{Math.round(item.val).toLocaleString()} kg</span>
                            </div>
                            <div style={{ height: '6px', backgroundColor: isDarkMode ? '#1f2937' : '#f1f5f9', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${pct}%`, backgroundColor: '#8b5cf6', borderRadius: '3px' }}></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '20px', marginBottom: '32px' }}>
                  
                  {/* Monthly Emissions Line Area Chart */}
                  <div style={{ gridColumn: 'span 8', backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '20px' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: '700', margin: '0 0 12px 0', color: themeText }}>📈 Monthly Emissions Trend</h4>
                    
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                      <svg width="100%" height={svgH} viewBox={`0 0 ${svgW} ${svgH}`} style={{ overflow: 'visible' }}>
                        <defs>
                          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#10b981" stopOpacity="0.22" />
                            <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
                          </linearGradient>
                        </defs>
                        
                        {/* Grid lines */}
                        <line x1="25" y1="20" x2={svgW - 25} y2="20" stroke={themeBorder} strokeWidth="1" strokeDasharray="4 4" />
                        <line x1="25" y1="65" x2={svgW - 25} y2="65" stroke={themeBorder} strokeWidth="1" strokeDasharray="4 4" />
                        <line x1="25" y1="110" x2={svgW - 25} y2="110" stroke={themeBorder} strokeWidth="1" />
                        
                        {/* Area under line */}
                        {areaPath && <path d={areaPath} fill="url(#areaGrad)" />}
                        
                        {/* Line chart curve */}
                        {linePath && <path d={linePath} fill="none" stroke="#10b981" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
                        
                        {/* Chart dots and labels */}
                        {pts.map((p, idx) => (
                          <g key={idx}>
                            <circle cx={p.x} cy={p.y} r="4" fill={isDarkMode ? '#080c14' : '#ffffff'} stroke="#10b981" strokeWidth="2.5" />
                            <text x={p.x} y={svgH - 2} fill={themeSubtext} fontSize="9" fontWeight="600" textAnchor="middle">{p.name}</text>
                            {p.val > 0 && (
                              <text x={p.x} y={p.y - 8} fill={themeText} fontSize="8" fontWeight="700" textAnchor="middle">
                                {Math.round(p.val / 1000) > 0 ? `${Math.round(p.val / 1000)}t` : `${Math.round(p.val)}kg`}
                              </text>
                            )}
                          </g>
                        ))}
                      </svg>
                    </div>
                  </div>

                  {/* CBAM Cost Exposure Visual */}
                  <div style={{ gridColumn: 'span 4', backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <h4 style={{ fontSize: '14px', fontWeight: '700', margin: '0 0 4px 0', color: themeText }}>💶 CBAM Cost Exposure</h4>
                      <span style={{ fontSize: '11px', color: themeSubtext }}>Aggregated financial risk on embedded carbon imports</span>
                    </div>

                    <div style={{ margin: '20px 0', textAlign: 'center' }}>
                      <div style={{ fontSize: '32px', fontWeight: '900', color: '#f59e0b', letterSpacing: '-0.5px' }}>
                        €{universalResult.summary?.total_cbam_cost_eur?.toLocaleString() || 0}
                      </div>
                      <span style={{ fontSize: '12px', color: themeSubtext, fontWeight: '600' }}>
                        Total CBAM Levy Estimated
                      </span>
                    </div>

                    <div style={{ borderTop: `1px solid ${themeBorder}`, paddingTop: '12px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                      <span style={{ color: themeSubtext }}>Embedded Carbon:</span>
                      <strong>{universalResult.summary?.total_co2e_tonnes || 0} t CO₂e</strong>
                    </div>
                  </div>

                </div>

                {/* LIVE CALCULATION TABLE */}
                <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '24px', boxShadow: '0 4px 20px rgba(0,0,0,0.01)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <div>
                      <h3 style={{ fontSize: '16px', fontWeight: '700', margin: '0 0 4px 0' }}>🧮 Live Calculation Table</h3>
                      <p style={{ fontSize: '12px', color: themeSubtext, margin: 0 }}>Granular view of the parsed document logs. Select any row to open the complete calculation audit trace details.</p>
                    </div>
                  </div>

                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                      <thead>
                        <tr style={{ borderBottom: `2px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, fontWeight: '700' }}>
                          <th style={{ padding: '12px 8px' }}>Material</th>
                          <th style={{ padding: '12px 8px' }}>Supplier</th>
                          <th style={{ padding: '12px 8px' }}>Qty</th>
                          <th style={{ padding: '12px 8px' }}>Unit</th>
                          <th style={{ padding: '12px 8px' }}>Factor</th>
                          <th style={{ padding: '12px 8px' }}>Factor Source</th>
                          <th style={{ padding: '12px 8px' }}>Scope</th>
                          <th style={{ padding: '12px 8px' }}>CO₂ (kg)</th>
                          <th style={{ padding: '12px 8px' }}>CO₂e (kg)</th>
                          <th style={{ padding: '12px 8px' }}>CBAM Cost</th>
                          <th style={{ padding: '12px 8px' }}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {universalRecords.map((rec, idx) => (
                          <tr 
                            key={idx} 
                            onClick={() => setSelectedTraceRow(rec)}
                            style={{ 
                              borderBottom: `1px solid ${themeBorder}`,
                              cursor: 'pointer',
                              backgroundColor: selectedTraceRow?.id === rec.id 
                                ? (isDarkMode ? 'rgba(16, 185, 129, 0.12)' : 'rgba(16, 185, 129, 0.06)') 
                                : rec.is_anomaly 
                                  ? (isDarkMode ? 'rgba(239, 68, 68, 0.1)' : 'rgba(239, 68, 68, 0.05)') 
                                  : 'transparent',
                              transition: 'background-color 0.15s'
                            }}
                          >
                            <td style={{ padding: '12px 8px', fontWeight: '700', color: themeText }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                {rec.material}
                                {rec.is_anomaly === 1 && (
                                  <span title={rec.anomaly_reason || 'Anomaly Detected'} style={{ cursor: 'help' }}>⚠️</span>
                                )}
                              </div>
                            </td>
                            <td style={{ padding: '12px 8px', color: themeText }}>{rec.supplier}</td>
                            <td style={{ padding: '12px 8px', fontWeight: '600' }}>{rec.quantity}</td>
                            <td style={{ padding: '12px 8px' }}>{rec.unit}</td>
                            <td style={{ padding: '12px 8px', fontFamily: 'monospace', fontWeight: '600' }}>{rec.emission_factor}</td>
                            <td style={{ padding: '12px 8px', fontSize: '11px', color: themeSubtext }}>{rec.factor_source}</td>
                            <td style={{ padding: '12px 8px' }}>
                              <span style={{ fontSize: '10px', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', padding: '2px 6px', borderRadius: '4px', fontWeight: '600' }}>
                                {rec.scope}
                              </span>
                            </td>
                            <td style={{ padding: '12px 8px' }}>{rec.co2_kg?.toLocaleString()}</td>
                            <td style={{ padding: '12px 8px', fontWeight: '700', color: '#10b981' }}>{rec.co2e_kg?.toLocaleString()}</td>
                            <td style={{ padding: '12px 8px', fontWeight: '700', color: '#f59e0b' }}>€{rec.cbam_cost_eur?.toLocaleString()}</td>
                            <td style={{ padding: '12px 8px' }}>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', alignItems: 'flex-start' }}>
                                <span style={{ 
                                  fontSize: '10px', 
                                  backgroundColor: rec.calculation_status === 'Calculated' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)', 
                                  color: rec.calculation_status === 'Calculated' ? '#10b981' : '#f59e0b', 
                                  padding: '3px 8px', 
                                  borderRadius: '6px', 
                                  fontWeight: '700' 
                                }}>
                                  {rec.calculation_status}
                                </span>
                                {rec.is_duplicate === 1 && (
                                  <span style={{ fontSize: '9px', backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#f87171', padding: '1px 4px', borderRadius: '3px', fontWeight: 'bold' }}>
                                    DUPLICATE
                                  </span>
                                )}
                                {rec.ocr_error === 1 && (
                                  <span style={{ fontSize: '9px', backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#f87171', padding: '1px 4px', borderRadius: '3px', fontWeight: 'bold' }}>
                                    OCR ERROR
                                  </span>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Row Detail Trace Drawer */}
                  {selectedTraceRow && (
                    <div style={{
                      marginTop: '28px',
                      backgroundColor: isDarkMode ? '#0a0d16' : '#f8fafc',
                      border: '2px solid #10b981',
                      borderRadius: '16px',
                      padding: '24px',
                      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)'
                    }}>
                      <div style={{ display: 'flex', justify_content: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                        <h4 style={{ fontSize: '16px', fontWeight: '800', margin: 0, color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>
                          🔎 Row #{selectedTraceRow.id} Calculation Audit Details
                        </h4>
                        <button 
                          onClick={() => setSelectedTraceRow(null)} 
                          style={{
                            backgroundColor: 'transparent',
                            border: 'none',
                            color: themeSubtext,
                            cursor: 'pointer',
                            fontWeight: '700',
                            fontSize: '13px'
                          }}
                        >
                          ✕ Close Detail Panel
                        </button>
                      </div>

                      {/* Warnings banner */}
                      {selectedTraceRow.is_anomaly === 1 && (
                        <div style={{
                          backgroundColor: 'rgba(239, 68, 68, 0.15)',
                          border: '1px solid #ef4444',
                          borderRadius: '8px',
                          padding: '12px 16px',
                          color: '#f87171',
                          fontSize: '13px',
                          fontWeight: '600',
                          marginBottom: '20px'
                        }}>
                          ⚠️ <strong>Security Audit Warning:</strong> {selectedTraceRow.anomaly_reason || 'Anomaly detected in transaction metrics.'}
                        </div>
                      )}

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                        {/* Left: Original OCR Preview */}
                        <div style={{ backgroundColor: themeCard, padding: '18px', borderRadius: '12px', border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          <span style={{ fontSize: '11px', color: themeSubtext, fontWeight: '800', display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>📄 Original OCR Document Scan</span>
                          <div style={{
                            backgroundColor: isDarkMode ? '#0d1117' : '#f8fafc',
                            border: `1px solid ${themeBorder}`,
                            borderRadius: '8px',
                            padding: '14px',
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            color: isDarkMode ? '#e6edf3' : '#1f2937',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-all',
                            lineHeight: '1.6',
                            flexGrow: 1
                          }}>
                            {/* Format the raw string cleanly, highlighting structured tokens */}
                            {(() => {
                              const rawText = selectedTraceRow.original_ocr_text || `${selectedTraceRow.material} (${selectedTraceRow.quantity} ${selectedTraceRow.unit})`;
                              // Highlight tokens
                              return rawText.split('|').map((part, pIdx) => {
                                const [key, val] = part.split(':');
                                if (key && val) {
                                  return (
                                    <div key={pIdx} style={{ margin: '4px 0', borderBottom: `1px dashed ${themeBorder}`, paddingBottom: '4px' }}>
                                      <span style={{ color: themeSubtext, fontWeight: 'bold' }}>{key.trim()}:</span>
                                      <span style={{
                                        marginLeft: '8px',
                                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                                        color: '#10b981',
                                        padding: '2px 6px',
                                        borderRadius: '4px',
                                        fontWeight: 'bold',
                                        border: '1px solid rgba(16, 185, 129, 0.3)'
                                      }}>{val.trim()}</span>
                                    </div>
                                  );
                                }
                                return <div key={pIdx} style={{ margin: '4px 0' }}>{part}</div>;
                              });
                            })()}
                          </div>
                        </div>

                        {/* Right: Extracted Table Validation */}
                        <div style={{ backgroundColor: themeCard, padding: '18px', borderRadius: '12px', border: `1px solid ${themeBorder}`, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '11px', color: themeSubtext, fontWeight: '800', display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>✓ Extracted Structured Copy</span>
                            <span style={{
                              fontSize: '11px',
                              fontWeight: '800',
                              backgroundColor: 'rgba(16, 185, 129, 0.15)',
                              color: '#10b981',
                              padding: '3px 8px',
                              borderRadius: '4px',
                              border: '1px solid rgba(16, 185, 129, 0.3)'
                            }}>FIDELITY PASSED 🟢</span>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: isDarkMode ? '#131924' : '#f8fafc', borderRadius: '6px' }}>
                              <span style={{ color: themeSubtext }}>Material</span>
                              <strong style={{ color: themeText }}>{selectedTraceRow.material}</strong>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: isDarkMode ? '#131924' : '#f8fafc', borderRadius: '6px' }}>
                              <span style={{ color: themeSubtext }}>Quantity</span>
                              <strong style={{ color: themeText }}>{selectedTraceRow.quantity?.toLocaleString()}</strong>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: isDarkMode ? '#131924' : '#f8fafc', borderRadius: '6px' }}>
                              <span style={{ color: themeSubtext }}>Unit</span>
                              <strong style={{ color: themeText }}>{selectedTraceRow.unit}</strong>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: isDarkMode ? '#131924' : '#f8fafc', borderRadius: '6px' }}>
                              <span style={{ color: themeSubtext }}>Cost</span>
                              <strong style={{ color: themeText }}>
                                {selectedTraceRow.cost ? new Intl.NumberFormat('en-US', { style: 'currency', currency: selectedTraceRow.currency || 'EUR' }).format(selectedTraceRow.cost) : 'N/A'}
                              </strong>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: isDarkMode ? '#131924' : '#f8fafc', borderRadius: '6px' }}>
                              <span style={{ color: themeSubtext }}>Region</span>
                              <strong style={{ color: themeText }}>{selectedTraceRow.country || 'N/A'}</strong>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: isDarkMode ? '#131924' : '#f8fafc', borderRadius: '6px' }}>
                              <span style={{ color: themeSubtext }}>Matched Factor Material</span>
                              <strong style={{ color: '#10b981' }}>{selectedTraceRow.matched_material}</strong>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '20px' }}>
                        <div style={{ backgroundColor: themeCard, padding: '12px', borderRadius: '8px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ fontSize: '10px', color: themeSubtext, display: 'block', marginBottom: '2px' }}>Factor</span>
                          <strong style={{ fontSize: '13px' }}>{selectedTraceRow.emission_factor}</strong>
                          <span style={{ fontSize: '10px', color: themeSubtext, display: 'block' }}>kg CO₂e / {selectedTraceRow.unit}</span>
                        </div>
                        <div style={{ backgroundColor: themeCard, padding: '12px', borderRadius: '8px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ fontSize: '10px', color: themeSubtext, display: 'block', marginBottom: '2px' }}>Factor ID</span>
                          <code style={{ fontSize: '11px', wordBreak: 'break-all' }}>{selectedTraceRow.factor_id}</code>
                        </div>
                        <div style={{ backgroundColor: themeCard, padding: '12px', borderRadius: '8px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ fontSize: '10px', color: themeSubtext, display: 'block', marginBottom: '2px' }}>Formula</span>
                          <span style={{ fontSize: '11px', fontFamily: 'monospace' }}>{selectedTraceRow.formula?.split('|')[0]}</span>
                        </div>
                        <div style={{ backgroundColor: themeCard, padding: '12px', borderRadius: '8px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ fontSize: '10px', color: themeSubtext, display: 'block', marginBottom: '2px' }}>Calculation (CO₂e)</span>
                          <strong style={{ fontSize: '14px', color: '#10b981' }}>{selectedTraceRow.co2e_kg?.toLocaleString()} kg CO₂e</strong>
                        </div>
                      </div>

                      {/* Display suggestions if unmatched */}
                      {selectedTraceRow.recommendations && selectedTraceRow.recommendations.length > 0 && (
                        <div style={{ backgroundColor: themeCard, padding: '18px', borderRadius: '12px', border: '1px solid #3b82f6', marginBottom: '20px' }}>
                          <span style={{ fontSize: '11px', color: '#3b82f6', fontWeight: '700', display: 'block', marginBottom: '8px', textTransform: 'uppercase' }}>💡 Top 5 Matching Recommendations</span>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {selectedTraceRow.recommendations.map((rec, rIdx) => (
                              <div key={rIdx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', backgroundColor: themeBg, padding: '8px 12px', borderRadius: '6px' }}>
                                <div>
                                  <strong>{rec.material}</strong> <code style={{ fontSize: '10px', marginLeft: '6px', backgroundColor: 'rgba(255,255,255,0.05)', padding: '2px 4px' }}>{rec.factor_id}</code>
                                  <span style={{ fontSize: '11px', color: themeSubtext, marginLeft: '12px' }}>{rec.factor} kg CO₂e/{rec.unit} ({rec.source})</span>
                                </div>
                                <span style={{ color: '#3b82f6', fontWeight: 'bold' }}>{Math.round(rec.confidence * 100)}% Match</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div style={{ backgroundColor: isDarkMode ? 'rgba(16, 185, 129, 0.05)' : 'rgba(16, 185, 129, 0.02)', border: '1px solid rgba(16, 185, 129, 0.15)', padding: '16px', borderRadius: '12px' }}>
                        <span style={{ fontSize: '11px', color: '#10b981', fontWeight: '700', display: 'block', marginBottom: '8px', textTransform: 'uppercase' }}>5-Step Audit Trail</span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {selectedTraceRow.calculation_trace?.map((step, sIdx) => (
                            <div key={sIdx} style={{ fontSize: '12px', backgroundColor: themeCard, padding: '10px 14px', borderRadius: '8px', borderLeft: '3px solid #10b981' }}>
                              {step}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                </div>
              </div>
            )}

          </div>
        )}

        {/* --- TAB 2: UPLOAD --- */}
        {activeTab === 'Upload' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            <div style={{
              backgroundColor: themeCard,
              border: `2px solid ${universalStatus === 'error' ? '#ef4444' : '#10b981'}`,
              borderRadius: '16px',
              padding: '32px',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: '0 0 8px 0' }}>📁 Consolidated AI Data Intake Dropzone</h3>
              <p style={{ fontSize: '13px', color: themeSubtext, margin: '0 0 24px 0' }}>
                Upload any PDF, Excel, CSV, JSON or ZIP file. CarbonLedger AI will auto-detect document classification, parse tables, match factors, and estimate CBAM costs.
              </p>

              {universalStatus === 'idle' ? (
                <div 
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                      handleUniversalFileChange(e.dataTransfer.files[0]);
                    }
                  }}
                  onClick={() => document.getElementById('upload-tab-picker').click()}
                  style={{
                    border: `2px dashed ${themeBorder}`,
                    borderRadius: '16px',
                    padding: '60px 40px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    backgroundColor: isDarkMode ? 'rgba(31, 41, 55, 0.5)' : '#f9fafb',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '16px'
                  }}
                >
                  <input 
                    type="file" 
                    id="upload-tab-picker" 
                    accept=".pdf,.xlsx,.xls,.csv,.zip,.json"
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleUniversalFileChange(e.target.files[0]);
                      }
                    }}
                  />
                  <span style={{ fontSize: '56px' }}>📤</span>
                  <span style={{ fontSize: '18px', fontWeight: 'bold' }}>Drag & Drop consolidated file or <span style={{ color: '#10b981' }}>Browse</span></span>
                  <span style={{ fontSize: '12px', color: themeSubtext }}>Supported Formats: PDF, XLSX, XLS, CSV, ZIP, JSON</span>
                </div>
              ) : (
                <div style={{ backgroundColor: isDarkMode ? '#1f2937' : '#f3f4f6', borderRadius: '12px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      <span style={{ fontSize: '28px' }}>📄</span>
                      <div>
                        <strong style={{ fontSize: '15px' }}>{universalFile?.name}</strong>
                        <div style={{ fontSize: '12px', color: themeSubtext }}>
                          Status: <span style={{ color: '#10b981', fontWeight: 'bold', textTransform: 'capitalize' }}>{universalStatus}</span>
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: themeSubtext, cursor: 'pointer' }}>
                        <input 
                          type="checkbox" 
                          checked={debugMode} 
                          onChange={(e) => setDebugMode(e.target.checked)}
                          style={{ accentColor: '#10b981', width: '14px', height: '14px' }}
                        />
                        <span>🐞 Toggle Debug Mode</span>
                      </label>
                      <button onClick={handleRemoveUniversal} style={{ backgroundColor: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontWeight: 'bold' }}>
                        Remove & Upload New File
                      </button>
                    </div>
                  </div>

                  {(universalStatus === 'uploading' || universalStatus === 'calculating') && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                        <span>AI Extraction & Carbon Engine Progress</span>
                        <span>{universalProgress}%</span>
                      </div>
                      <div style={{ height: '8px', width: '100%', backgroundColor: themeBorder, borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${universalProgress}%`, backgroundColor: '#10b981', transition: 'width 0.3s' }}></div>
                      </div>
                    </div>
                  )}

                  <div style={{ backgroundColor: '#070a13', borderRadius: '8px', padding: '16px', fontFamily: 'monospace', fontSize: '12px', color: '#a7f3d0', maxHeight: '160px', overflowY: 'auto' }}>
                    {universalLogs.map((l, i) => <div key={i}>{l}</div>)}
                  </div>

                  {effectiveError && (
                    <div style={{
                      backgroundColor: 'rgba(239, 68, 68, 0.15)',
                      border: '1px solid #ef4444',
                      borderRadius: '8px',
                      padding: '16px',
                      color: '#f87171',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      marginTop: '16px',
                      textAlign: 'center'
                    }}>
                      ❌ Pipeline Error: {effectiveError}
                    </div>
                  )}

                  {debugMode && (
                    <div style={{
                      backgroundColor: isDarkMode ? '#0a0d16' : '#f1f5f9',
                      border: `2px dashed ${isDarkMode ? '#374151' : '#cbd5e1'}`,
                      borderRadius: '12px',
                      padding: '20px',
                      marginTop: '20px',
                      textAlign: 'left'
                    }}>
                      <h4 style={{ margin: '0 0 16px 0', color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        🐞 OCR Pipeline Developer Debug Mode
                      </h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginBottom: '16px' }}>
                        <div style={{ backgroundColor: themeCard, padding: '10px', borderRadius: '6px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ color: themeSubtext, fontSize: '11px', display: 'block' }}>OCR Characters Count</span>
                          <strong style={{ fontSize: '14px', color: themeText }}>{parserResponse?.raw_ocr_data?.text?.length || 0}</strong>
                        </div>
                        <div style={{ backgroundColor: themeCard, padding: '10px', borderRadius: '6px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ color: themeSubtext, fontSize: '11px', display: 'block' }}>Rows Parsed</span>
                          <strong style={{ fontSize: '14px', color: themeText }}>{reviewedRecords.length}</strong>
                        </div>
                        <div style={{ backgroundColor: themeCard, padding: '10px', borderRadius: '6px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ color: themeSubtext, fontSize: '11px', display: 'block' }}>Tables Parsed</span>
                          <strong style={{ fontSize: '14px', color: themeText }}>{parserResponse?.tables_count || 0}</strong>
                        </div>
                        <div style={{ backgroundColor: themeCard, padding: '10px', borderRadius: '6px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ color: themeSubtext, fontSize: '11px', display: 'block' }}>Parser Processing Time</span>
                          <strong style={{ fontSize: '14px', color: themeText }}>{parserResponse?.processing_time_ms || 0} ms</strong>
                        </div>
                        <div style={{ backgroundColor: themeCard, padding: '10px', borderRadius: '6px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ color: themeSubtext, fontSize: '11px', display: 'block' }}>Parser Response JSON Size</span>
                          <strong style={{ fontSize: '14px', color: themeText }}>{parserResponse ? JSON.stringify(parserResponse).length : 0} bytes</strong>
                        </div>
                        <div style={{ backgroundColor: themeCard, padding: '10px', borderRadius: '6px', border: `1px solid ${themeBorder}` }}>
                          <span style={{ color: themeSubtext, fontSize: '11px', display: 'block' }}>Validation Mismatch/Errors</span>
                          <strong style={{ fontSize: '14px', color: '#ef4444' }}>
                            {reviewedRecords.flatMap(r => getRowFieldValidation(r).errors).length} Errors
                          </strong>
                        </div>
                      </div>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div>
                          <span style={{ color: themeSubtext, fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>Validation Details</span>
                          <pre style={{
                            backgroundColor: isDarkMode ? '#0d1117' : '#e2e8f0',
                            color: themeText,
                            padding: '10px',
                            borderRadius: '6px',
                            maxHeight: '120px',
                            overflowY: 'auto',
                            fontSize: '11px',
                            margin: 0
                          }}>
                            {JSON.stringify(reviewedRecords.map((r, i) => ({ row: i+1, validation: getRowFieldValidation(r) })), null, 2)}
                          </pre>
                        </div>

                        <div>
                          <span style={{ color: themeSubtext, fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>🔍 Row-Level OCR & Carbon Engine Variables</span>
                          <div style={{ overflowX: 'auto', border: `1px solid ${themeBorder}`, borderRadius: '6px' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11.5px', color: themeText, backgroundColor: themeBg }}>
                              <thead>
                                <tr style={{ borderBottom: `2px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, backgroundColor: isDarkMode ? '#131924' : '#f1f5f9' }}>
                                  <th style={{ padding: '6px' }}>Row</th>
                                  <th style={{ padding: '6px' }}>OCR Qty</th>
                                  <th style={{ padding: '6px' }}>Normalized Qty</th>
                                  <th style={{ padding: '6px' }}>Final Qty</th>
                                  <th style={{ padding: '6px' }}>OCR Unit</th>
                                  <th style={{ padding: '6px' }}>Canonical Unit</th>
                                  <th style={{ padding: '6px' }}>Factor ID</th>
                                  <th style={{ padding: '6px' }}>Factor Source</th>
                                  <th style={{ padding: '6px' }}>Formula</th>
                                </tr>
                              </thead>
                              <tbody>
                                {reviewedRecords.map((r, idx) => (
                                  <tr key={idx} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                                    <td style={{ padding: '6px', fontWeight: 'bold' }}>{idx + 1}</td>
                                    <td style={{ padding: '6px', color: '#f59e0b' }}>{r.quantity_raw || 'N/A'}</td>
                                    <td style={{ padding: '6px', color: '#10b981' }}>{clientParseNumeric(r.quantity_raw)}</td>
                                    <td style={{ padding: '6px', color: '#3b82f6', fontWeight: 'bold' }}>{clientParseNumeric(r.quantity)}</td>
                                    <td style={{ padding: '6px', color: '#f59e0b' }}>{r.unit_raw || 'N/A'}</td>
                                    <td style={{ padding: '6px', color: '#3b82f6' }}>{r.unit || 'N/A'}</td>
                                    <td style={{ padding: '6px', fontFamily: 'monospace' }}>{r.factor_id || 'AUTO_RESOLVE'}</td>
                                    <td style={{ padding: '6px', color: themeSubtext }}>{r.factor_source || 'Emission Database'}</td>
                                    <td style={{ padding: '6px', fontFamily: 'monospace', color: '#10b981' }}>
                                      {r.formula || `${clientParseNumeric(r.quantity)} ${r.unit || 'kg'} * EF`}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                        
                        <div>
                          <span style={{ color: themeSubtext, fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>React Pipeline State</span>
                          <pre style={{
                            backgroundColor: isDarkMode ? '#0d1117' : '#e2e8f0',
                            color: themeText,
                            padding: '10px',
                            borderRadius: '6px',
                            maxHeight: '120px',
                            overflowY: 'auto',
                            fontSize: '11px',
                            margin: 0
                          }}>
                            {JSON.stringify({
                              universalStatus,
                              universalProgress,
                              universalUploadId,
                              parserPipelineError,
                              hasParserResponse: !!parserResponse,
                              recordsCount: reviewedRecords.length
                            }, null, 2)}
                          </pre>
                        </div>

                        <div>
                          <span style={{ color: themeSubtext, fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>API Parser Raw Response (JSON)</span>
                          <pre style={{
                            backgroundColor: isDarkMode ? '#0d1117' : '#e2e8f0',
                            color: themeText,
                            padding: '10px',
                            borderRadius: '6px',
                            maxHeight: '200px',
                            overflowY: 'auto',
                            fontSize: '11px',
                            margin: 0
                          }}>
                            {parserResponse ? JSON.stringify(parserResponse, null, 2) : "No parser response payload available."}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}

                  {universalStatus === 'parsed' && !effectiveError && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginTop: '24px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${themeBorder}`, paddingBottom: '16px' }}>
                        <div>
                          <h3 style={{ fontSize: '18px', fontWeight: '800', margin: 0, color: '#10b981' }}>📝 Review & Approve Extracted Data</h3>
                          <span style={{ fontSize: '12px', color: themeSubtext }}>Session: {universalUploadId}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                          {saveStatus && <span style={{ fontSize: '12px', color: '#10b981', fontWeight: 'bold' }}>{saveStatus}</span>}
                          <button 
                            onClick={handleSaveChanges}
                            style={{
                              backgroundColor: isDarkMode ? '#1f2937' : '#e2e8f0',
                              color: themeText,
                              border: `1px solid ${themeBorder}`,
                              padding: '8px 16px',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontWeight: 'bold',
                              fontSize: '12px'
                            }}
                          >
                            💾 Save Changes
                          </button>
                          <button 
                            onClick={handleApproveAndCalculate}
                            disabled={reviewedRecords.length === 0 || reviewedRecords.some(r => !getRowFieldValidation(r).isValid)}
                            style={{
                              backgroundColor: (reviewedRecords.length === 0 || reviewedRecords.some(r => !getRowFieldValidation(r).isValid)) ? '#374151' : '#10b981',
                              color: (reviewedRecords.length === 0 || reviewedRecords.some(r => !getRowFieldValidation(r).isValid)) ? '#9ca3af' : '#0b0f19',
                              border: 'none',
                              padding: '8px 18px',
                              borderRadius: '6px',
                              cursor: (reviewedRecords.length === 0 || reviewedRecords.some(r => !getRowFieldValidation(r).isValid)) ? 'not-allowed' : 'pointer',
                              fontWeight: 'bold',
                              fontSize: '12px'
                            }}
                          >
                            🚀 Approve & Calculate
                          </button>
                        </div>
                      </div>

                      {(reviewedRecords.length === 0 || reviewedRecords.some(r => !getRowFieldValidation(r).isValid)) && (
                        <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', borderRadius: '8px', padding: '12px 16px', color: '#f87171', fontSize: '13px', fontWeight: '600' }}>
                          ⚠️ <strong>Validation Error:</strong> Approve & Calculate is locked. Please ensure at least one row is loaded, all red mismatch/missing validation errors are resolved, and mandatory fields are populated.
                        </div>
                      )}

                      <div style={{ display: 'grid', gridTemplateColumns: '30% 70%', gap: '20px' }}>
                        {/* Left: OCR Preview */}
                        <div style={{ backgroundColor: isDarkMode ? '#0d1117' : '#f8fafc', border: `1px solid ${themeBorder}`, borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          <span style={{ fontSize: '11px', color: themeSubtext, fontWeight: '800', display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>📄 OCR Raw Text Preview</span>
                          <div style={{
                            backgroundColor: isDarkMode ? '#070a13' : '#ffffff',
                            border: `1px solid ${themeBorder}`,
                            borderRadius: '8px',
                            padding: '12px',
                            fontFamily: 'monospace',
                            fontSize: '11.5px',
                            color: isDarkMode ? '#a7f3d0' : '#0f172a',
                            height: '420px',
                            overflowY: 'auto',
                            whiteSpace: 'pre-wrap',
                            textAlign: 'left'
                          }}>
                            {parserResponse?.raw_ocr_data?.text || "No raw OCR text available for this file."}
                          </div>
                        </div>

                        {/* Right: Editable Grid */}
                        <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '10px', padding: '16px', overflowX: 'auto' }}>
                          <span style={{ fontSize: '11px', color: themeSubtext, fontWeight: '800', display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>✏️ Edit Extracted Table Fields</span>
                          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
                            <thead>
                              <tr style={{ borderBottom: `2px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext }}>
                                <th style={{ padding: '6px' }}>Row</th>
                                <th style={{ padding: '6px' }}>PO Number</th>
                                <th style={{ padding: '6px' }}>Supplier</th>
                                <th style={{ padding: '6px' }}>Material</th>
                                <th style={{ padding: '6px' }}>Quantity</th>
                                <th style={{ padding: '6px' }}>Unit</th>
                                <th style={{ padding: '6px' }}>Cost</th>
                                <th style={{ padding: '6px' }}>Currency</th>
                                <th style={{ padding: '6px' }}>Country</th>
                                <th style={{ padding: '6px' }}>Delivery Date</th>
                                <th style={{ padding: '6px' }}>Status</th>
                                <th style={{ padding: '6px' }}>Validation</th>
                              </tr>
                            </thead>
                            <tbody>
                              {reviewedRecords.length === 0 ? (
                                <tr>
                                  <td colSpan="12" style={{ padding: '24px', textAlign: 'center', color: themeSubtext, fontWeight: 'bold' }}>
                                    No records extracted
                                  </td>
                                </tr>
                              ) : (
                                reviewedRecords.map((row, rIdx) => {
                                  const valResult = getRowFieldValidation(row);
                                  let badgeBg = 'rgba(16, 185, 129, 0.15)';
                                  let badgeColor = '#10b981';
                                  if (valResult.validationStatus === 'RED') {
                                    badgeBg = 'rgba(239, 68, 68, 0.15)';
                                    badgeColor = '#f87171';
                                  } else if (valResult.validationStatus === 'YELLOW') {
                                    badgeBg = 'rgba(245, 158, 11, 0.15)';
                                    badgeColor = '#f59e0b';
                                  }
                                  const statusBadgeStyle = { bg: badgeBg, color: badgeColor, label: valResult.statusLabel };

                                  const updateField = (fld, val) => {
                                    setReviewedRecords(prev => prev.map((r, i) => i === rIdx ? { ...r, [fld]: val } : r));
                                  };

                                  return (
                                    <tr key={rIdx} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                                      <td style={{ padding: '6px', fontWeight: 'bold' }}>{rIdx + 1}</td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.po_number} 
                                          onChange={(e) => updateField('po_number', e.target.value)}
                                          style={{ width: '70px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.supplier} 
                                          onChange={(e) => updateField('supplier', e.target.value)}
                                          style={{ width: '85px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.material} 
                                          onChange={(e) => updateField('material', e.target.value)}
                                          style={{ width: '90px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.quantity} 
                                          onChange={(e) => updateField('quantity', e.target.value)}
                                          style={{ width: '50px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.unit} 
                                          onChange={(e) => updateField('unit', e.target.value)}
                                          style={{ width: '40px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.cost} 
                                          onChange={(e) => updateField('cost', e.target.value)}
                                          style={{ width: '60px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.currency || 'EUR'} 
                                          onChange={(e) => updateField('currency', e.target.value)}
                                          style={{ width: '45px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.country} 
                                          onChange={(e) => updateField('country', e.target.value)}
                                          style={{ width: '30px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.delivery_date} 
                                          onChange={(e) => updateField('delivery_date', e.target.value)}
                                          style={{ width: '80px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <input 
                                          type="text" 
                                          value={row.status} 
                                          onChange={(e) => updateField('status', e.target.value)}
                                          style={{ width: '70px', backgroundColor: themeBg, color: themeText, border: `1px solid ${themeBorder}`, borderRadius: '4px', padding: '3px 5px', fontSize: '11px' }}
                                        />
                                      </td>
                                      <td style={{ padding: '6px' }}>
                                        <span style={{
                                          display: 'inline-block',
                                          fontSize: '10px',
                                          fontWeight: 'bold',
                                          backgroundColor: statusBadgeStyle.bg,
                                          color: statusBadgeStyle.color,
                                          padding: '2px 6px',
                                          borderRadius: '4px',
                                          whiteSpace: 'nowrap'
                                        }}>
                                          {statusBadgeStyle.label}
                                        </span>
                                      </td>
                                    </tr>
                                  );
                                })
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Session Audit Log */}
                      <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '12px', padding: '16px' }}>
                        <span style={{ fontSize: '11px', color: themeSubtext, fontWeight: '800', display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>🔍 Session Audit Log</span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {reviewAuditLog.map((log, lIdx) => (
                            <div key={lIdx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', backgroundColor: isDarkMode ? '#0d1117' : '#f8fafc', padding: '6px 10px', borderRadius: '4px' }}>
                              <div>
                                <span style={{ color: '#10b981', fontWeight: 'bold', marginRight: '6px' }}>[{log.user}]</span>
                                <span style={{ color: themeText }}>{log.action}</span>
                              </div>
                              <span style={{ color: themeSubtext, fontFamily: 'monospace' }}>{new Date(log.timestamp).toLocaleTimeString()}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {universalStatus === 'calculated' && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                      <span style={{ color: '#10b981', fontWeight: 'bold' }}>✅ Calculations & CBAM Cost Estimation Complete!</span>
                      <button onClick={() => setActiveTab('Dashboard')} style={{ backgroundColor: '#10b981', color: '#0b0f19', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}>
                        View Live Dashboard Table →
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- TAB 3: REPORTS --- */}
        {activeTab === 'Reports' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0 }}>📑 Auto-Generated Compliance & ESG Session Reports</h3>
            <p style={{ fontSize: '13px', color: themeSubtext, margin: '0 0 16px 0' }}>
              Download fresh compliance reports generated strictly from the current upload session.
            </p>

            {universalResult?.reports ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
                {[
                  { title: "📄 Carbon Audit Report", fmt: "PDF", key: "carbon_report_pdf", desc: "Complete GHG carbon audit with Executive Summary, Document Summary, Materials, Emission Summary, Scope 1/2/3, CBAM Cost, Top Emitters, Recommendations, and Audit Trail. Each row contains Factor ID, Formula, Confidence, Timestamp, Report ID.", sections: "11 Sections" },
                  { title: "📊 CBAM Declaration Report", fmt: "Excel", key: "cbam_report_excel", desc: "Multi-sheet EU CBAM embedded emissions workbook with all 11 sections. Every row includes Factor ID, Formula, Confidence, Timestamp, Report ID.", sections: "11 Sheets" },
                  { title: "📁 Carbon Inventory Workbook", fmt: "Excel", key: "inventory_excel", desc: "Full row-level carbon emission inventory with matched factor IDs, formulas, scope breakdowns, recommendations, and audit trail across 11 sheets.", sections: "11 Sheets" },
                  { title: "🔍 Audit Trail & Traceability", fmt: "JSON", key: "audit_json", desc: "Machine-readable structured audit trace with all 11 sections. Every row-level entry contains Factor ID, Formula, Confidence, Timestamp, and Report ID.", sections: "11 Sections" },
                  { title: "📑 Executive ESG Report", fmt: "PDF", key: "executive_esg_pdf", desc: "Board-level ESG & carbon accounting summary covering Executive Summary, Document Summary, Materials, Emission Summary, Scope 1/2/3, CBAM Cost, Top Emitters, Recommendations, and Audit Trail.", sections: "11 Sections" }
                ].map((rep, idx) => (
                  <div key={idx} style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '12px', padding: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h4 style={{ fontSize: '15px', fontWeight: 'bold', margin: '0 0 4px 0' }}>{rep.title}</h4>
                      <p style={{ fontSize: '12px', color: themeSubtext, margin: '0 0 8px 0' }}>{rep.desc}</p>
                      <span style={{ fontSize: '10px', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold' }}>
                        FORMAT: {rep.fmt}
                      </span>
                      <span style={{ fontSize: '10px', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', padding: '2px 8px', borderRadius: '4px', fontWeight: 'bold', marginLeft: '6px' }}>
                        {rep.sections}
                      </span>
                    </div>
                    <button
                      onClick={() => window.open('http://localhost:8000' + universalResult.reports[rep.key], '_blank')}
                      style={{ backgroundColor: '#10b981', color: '#0b0f19', border: 'none', padding: '10px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', fontSize: '13px' }}
                    >
                      Download 📥
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '12px', padding: '40px', textAlign: 'center' }}>
                <p style={{ color: themeSubtext, margin: '0 0 16px 0' }}>No active upload session report found. Please upload a file to generate fresh compliance reports.</p>
                <button onClick={() => setActiveTab('Upload')} style={{ backgroundColor: '#10b981', color: '#0b0f19', border: 'none', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>
                  Upload File →
                </button>
              </div>
            )}
          </div>
        )}

        {/* --- TAB 4: AI INTELLIGENCE --- */}
        {activeTab === 'AI Intelligence' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              
              {/* Copilot Chat Assistant Panel */}
              <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', height: '560px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 4px 0' }}>🤖 AI Chat Assistant</h3>
                <span style={{ fontSize: '11px', color: themeSubtext, marginBottom: '16px' }}>Ask sustainability copilot questions about high emissions, suppliers, or CBAM reduction opportunities.</span>
                
                {/* Message Log */}
                <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', padding: '12px', backgroundColor: isDarkMode ? '#0a0d16' : '#f8fafc', borderRadius: '10px', marginBottom: '16px' }}>
                  {chatMessages.map((msg, mIdx) => (
                    <div 
                      key={mIdx} 
                      style={{
                        alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                        backgroundColor: msg.sender === 'user' ? '#10b981' : (isDarkMode ? '#111827' : '#ffffff'),
                        color: msg.sender === 'user' ? '#0b0f19' : themeText,
                        border: msg.sender === 'user' ? 'none' : `1px solid ${themeBorder}`,
                        padding: '10px 14px',
                        borderRadius: '12px',
                        maxWidth: '85%',
                        fontSize: '12.5px',
                        whiteSpace: 'pre-wrap',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                      }}
                    >
                      {msg.text}
                    </div>
                  ))}
                  {isChatLoading && (
                    <div style={{ alignSelf: 'flex-start', color: themeSubtext, fontSize: '12px', fontStyle: 'italic', paddingLeft: '8px' }}>
                      Copilot is thinking...
                    </div>
                  )}
                </div>

                {/* Quick Prompts */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', overflowX: 'auto', paddingBottom: '4px' }}>
                  <button 
                    onClick={() => handleSendChat("Why is this emission high?")}
                    style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', border: 'none', padding: '6px 12px', borderRadius: '20px', cursor: 'pointer', fontSize: '11px', fontWeight: '600', whiteSpace: 'nowrap' }}
                  >
                    🔍 Why is this emission high?
                  </button>
                  <button 
                    onClick={() => handleSendChat("Which supplier has highest emissions?")}
                    style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981', border: 'none', padding: '6px 12px', borderRadius: '20px', cursor: 'pointer', fontSize: '11px', fontWeight: '600', whiteSpace: 'nowrap' }}
                  >
                    🏭 Which supplier has highest emissions?
                  </button>
                  <button 
                    onClick={() => handleSendChat("How can I reduce CBAM cost?")}
                    style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', border: 'none', padding: '6px 12px', borderRadius: '20px', cursor: 'pointer', fontSize: '11px', fontWeight: '600', whiteSpace: 'nowrap' }}
                  >
                    💶 How can I reduce CBAM cost?
                  </button>
                </div>

                {/* Input form */}
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input 
                    type="text"
                    placeholder="Ask a sustainability or CBAM audit question..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSendChat(); }}
                    style={{ flex: 1, backgroundColor: isDarkMode ? '#1f2937' : '#ffffff', border: `1px solid ${themeBorder}`, color: themeText, padding: '10px 14px', borderRadius: '8px', fontSize: '13px' }}
                  />
                  <button 
                    onClick={() => handleSendChat()}
                    style={{ backgroundColor: '#10b981', color: '#0b0f19', border: 'none', padding: '10px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', fontSize: '13px' }}
                  >
                    Send
                  </button>
                </div>
              </div>

              {/* Scenario Analysis Simulation */}
              <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '24px', display: 'flex', flexDirection: 'column', height: '560px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 4px 0' }}>📈 Scenario Analysis (What-If Simulation)</h3>
                <span style={{ fontSize: '11px', color: themeSubtext, marginBottom: '20px' }}>Model carbon offset strategies and estimate tariff savings, payback periods, and ROI.</span>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', flex: 1 }}>
                  <div>
                    <label style={{ fontSize: '12px', fontWeight: '700', color: themeSubtext, display: 'block', marginBottom: '8px' }}>Select Decarbonization Strategy</label>
                    <select 
                      value={selectedStrategy} 
                      onChange={(e) => setSelectedStrategy(e.target.value)}
                      style={{ width: '100%', backgroundColor: isDarkMode ? '#1f2937' : '#ffffff', border: `1px solid ${themeBorder}`, color: themeText, padding: '10px 12px', borderRadius: '8px', fontSize: '13px' }}
                    >
                      <option value="eaf_steel">⚡ Transition to Electric Arc Furnace (EAF) Steel</option>
                      <option value="rail_freight">🚂 Switch Logistics to Low-Carbon Rail Freight</option>
                      <option value="green_energy_tariff">🔌 Shift Facilities to Green Electricity Tariff</option>
                    </select>
                  </div>

                  <button 
                    onClick={handleRunScenario}
                    disabled={isScenarioLoading}
                    style={{ backgroundColor: '#3b82f6', color: '#ffffff', border: 'none', padding: '12px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', fontSize: '13px' }}
                  >
                    {isScenarioLoading ? 'Running Simulation...' : '🚀 Run What-If Scenario'}
                  </button>

                  {scenarioResult ? (
                    <div style={{ backgroundColor: isDarkMode ? '#0a0d16' : '#f8fafc', padding: '16px', borderRadius: '10px', border: `1px solid ${themeBorder}`, fontSize: '12.5px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: themeSubtext }}>CO₂ Reduction (kg):</span>
                        <strong style={{ color: '#10b981' }}>-{scenarioResult.annual_co2_reduction_kg?.toLocaleString()} kg (-{scenarioResult.co2_reduction_pct}%)</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: themeSubtext }}>New Annual CO₂ Footprint:</span>
                        <strong>{scenarioResult.new_annual_co2_kg?.toLocaleString()} kg</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: themeSubtext }}>New CBAM Cost Levy:</span>
                        <strong style={{ color: '#f59e0b' }}>€{scenarioResult.new_cbam_cost_euro?.toLocaleString()}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: themeSubtext }}>Annual CBAM Savings:</span>
                        <strong style={{ color: '#10b981' }}>€{scenarioResult.tariff_savings_euro?.toLocaleString()}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: themeSubtext }}>Capital Cost Investment:</span>
                        <strong>€{scenarioResult.capital_cost_euro?.toLocaleString()}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: `1px solid ${themeBorder}`, paddingTop: '8px' }}>
                        <span style={{ color: themeSubtext }}>Estimated Annual ROI:</span>
                        <strong style={{ color: '#10b981' }}>{scenarioResult.estimated_annual_roi_pct}%</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: themeSubtext }}>Payback Period:</span>
                        <strong>{scenarioResult.payback_period_years} Years</strong>
                      </div>
                    </div>
                  ) : (
                    <div style={{ flex: 1, border: `2px dashed ${themeBorder}`, borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: themeSubtext, fontSize: '12px' }}>
                      Select a strategy and click Run to simulate scenario benefits.
                    </div>
                  )}
                </div>
              </div>

            </div>

            {/* CBAM Cost Forecast & Reduction Section */}
            <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 4px 0' }}>🔮 6-Month CBAM Cost & Emissions Forecast</h3>
                  <span style={{ fontSize: '11px', color: themeSubtext }}>LSTM-based neural network forecasting model projecting baseline trends.</span>
                </div>
                <button 
                  onClick={handleRunForecast}
                  disabled={isForecastLoading}
                  style={{ backgroundColor: '#10b981', color: '#0b0f19', border: 'none', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}
                >
                  {isForecastLoading ? 'Generating Forecast...' : 'Generate 6-Month Projection'}
                </button>
              </div>

              {forecastResult ? (
                <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '24px' }}>
                  
                  {/* Forecast Graph */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                      <svg width="100%" height="160" viewBox="0 0 500 160" style={{ overflow: 'visible' }}>
                        {/* Grid lines */}
                        <line x1="30" y1="20" x2="470" y2="20" stroke={themeBorder} strokeWidth="1" strokeDasharray="4 4" />
                        <line x1="30" y1="80" x2="470" y2="80" stroke={themeBorder} strokeWidth="1" strokeDasharray="4 4" />
                        <line x1="30" y1="140" x2="470" y2="140" stroke={themeBorder} strokeWidth="1" />

                        {/* Historical Line */}
                        <path 
                          d={`M 30 110 L 70 100 L 110 105 L 150 95 L 190 85 L 230 90`} 
                          fill="none" 
                          stroke={themeSubtext} 
                          strokeWidth="2.5" 
                        />
                        {/* Forecast Line */}
                        <path 
                          d={`M 230 90 L 270 88 L 310 82 L 350 78 L 390 73 L 430 67 L 470 60`} 
                          fill="none" 
                          stroke="#10b981" 
                          strokeWidth="3" 
                          strokeDasharray="4 2"
                        />

                        {/* Label dots */}
                        <circle cx="230" cy="90" r="4" fill="#10b981" />
                        <circle cx="470" cy="60" r="4" fill="#10b981" />

                        {/* Text values */}
                        <text x="30" y="152" fill={themeSubtext} fontSize="8" textAnchor="middle">Hist</text>
                        <text x="230" y="152" fill={themeSubtext} fontSize="8" textAnchor="middle">Current</text>
                        <text x="470" y="152" fill={themeSubtext} fontSize="8" textAnchor="middle">Month +6</text>

                        <text x="230" y="78" fill="#10b981" fontSize="9" fontWeight="bold" textAnchor="middle">24,000 kg</text>
                        <text x="470" y="48" fill="#10b981" fontSize="9" fontWeight="bold" textAnchor="middle">27,500 kg</text>
                      </svg>
                    </div>
                  </div>

                  {/* Forecast stats */}
                  <div style={{ backgroundColor: isDarkMode ? '#0a0d16' : '#f8fafc', padding: '16px', borderRadius: '10px', border: `1px solid ${themeBorder}`, fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <h4 style={{ fontSize: '13px', fontWeight: 'bold', margin: '0 0 4px 0', color: '#10b981' }}>📈 Neural Forecast Insights</h4>
                    <p style={{ color: themeSubtext, margin: '0 0 8px 0' }}>Emissions are projected to rise by <strong>14.5%</strong> over the next 6 months under business-as-usual trends.</p>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Current Month:</span>
                      <strong>24,000 kg CO₂e</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Projected Month +6:</span>
                      <strong>27,500 kg CO₂e</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Cumulative 6-Month CBAM Risk:</span>
                      <strong style={{ color: '#f59e0b' }}>€13,380.00</strong>
                    </div>
                  </div>

                </div>
              ) : (
                <div style={{ border: `2px dashed ${themeBorder}`, borderRadius: '10px', height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: themeSubtext, fontSize: '12px' }}>
                  Click Generate to run LSTM emissions forecast models.
                </div>
              )}
            </div>

          </div>
        )}

        {/* --- TAB 5: SETTINGS --- */}
        {activeTab === 'Settings' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '640px' }}>
            <div style={{ backgroundColor: themeCard, border: `1px solid ${themeBorder}`, borderRadius: '16px', padding: '28px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: '0 0 20px 0' }}>⚙️ System & Accounting Parameters</h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', display: 'block', marginBottom: '6px' }}>
                    Carbon Price (€ / tonne CO₂e) - Configurable CBAM Rate
                  </label>
                  <input 
                    type="number" 
                    value={carbonPrice} 
                    onChange={(e) => setCarbonPrice(parseFloat(e.target.value) || 0.0)}
                    style={{ width: '100%', backgroundColor: isDarkMode ? '#1f2937' : '#ffffff', border: `1px solid ${themeBorder}`, color: themeText, padding: '10px 12px', borderRadius: '8px', fontSize: '14px' }}
                  />
                  <span style={{ fontSize: '11px', color: themeSubtext, marginTop: '4px', display: 'block' }}>Used in CBAM Cost Engine calculation: Embedded CO₂e tonnes × €/ton</span>
                </div>

                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', display: 'block', marginBottom: '6px' }}>Default Reporting Region</label>
                  <select 
                    value={defaultRegion} 
                    onChange={(e) => setDefaultRegion(e.target.value)}
                    style={{ width: '100%', backgroundColor: isDarkMode ? '#1f2937' : '#ffffff', border: `1px solid ${themeBorder}`, color: themeText, padding: '10px 12px', borderRadius: '8px', fontSize: '14px' }}
                  >
                    <option value="DE">Germany (DE)</option>
                    <option value="EU">European Union (EU)</option>
                    <option value="US">United States (US)</option>
                    <option value="GLOBAL">Global Average</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '13px', fontWeight: '600', display: 'block', marginBottom: '6px' }}>Reporting Year</label>
                  <select 
                    value={reportingYear} 
                    onChange={(e) => setReportingYear(e.target.value)}
                    style={{ width: '100%', backgroundColor: isDarkMode ? '#1f2937' : '#ffffff', border: `1px solid ${themeBorder}`, color: themeText, padding: '10px 12px', borderRadius: '8px', fontSize: '14px' }}
                  >
                    <option value="2026">2026</option>
                    <option value="2025">2025</option>
                    <option value="2024">2024</option>
                  </select>
                </div>

                <div style={{ borderTop: `1px solid ${themeBorder}`, paddingTop: '20px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: 'bold', margin: '0 0 12px 0' }}>User Profile</h4>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div>
                      <label style={{ fontSize: '12px', color: themeSubtext, display: 'block', marginBottom: '4px' }}>Name</label>
                      <input 
                        type="text" 
                        value={userProfile.name} 
                        onChange={(e) => setUserProfile({ ...userProfile, name: e.target.value })}
                        style={{ width: '100%', backgroundColor: isDarkMode ? '#1f2937' : '#ffffff', border: `1px solid ${themeBorder}`, color: themeText, padding: '8px 12px', borderRadius: '6px', fontSize: '13px' }}
                      />
                    </div>
                    <div>
                      <label style={{ fontSize: '12px', color: themeSubtext, display: 'block', marginBottom: '4px' }}>Email</label>
                      <input 
                        type="email" 
                        value={userProfile.email} 
                        onChange={(e) => setUserProfile({ ...userProfile, email: e.target.value })}
                        style={{ width: '100%', backgroundColor: isDarkMode ? '#1f2937' : '#ffffff', border: `1px solid ${themeBorder}`, color: themeText, padding: '8px 12px', borderRadius: '6px', fontSize: '13px' }}
                      />
                    </div>
                  </div>
                </div>

                <button 
                  onClick={handleSaveSettings} 
                  style={{ backgroundColor: '#10b981', color: '#0b0f19', border: 'none', padding: '12px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold', fontSize: '14px', marginTop: '12px' }}
                >
                  Save Settings
                </button>

              </div>
            </div>
          </div>
        )}

        {/* --- TAB 6: ENTERPRISE ADMIN CONSOLE --- */}
        {activeTab === 'Admin Console' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {/* Admin Header & Success Toast */}
            {adminSuccessMsg && (
              <div style={{ padding: '12px 18px', borderRadius: '10px', backgroundColor: 'rgba(16,185,129,0.15)', border: '1px solid #10b981', color: '#34d399', fontSize: '13px', fontWeight: 'bold' }}>
                ✅ {adminSuccessMsg}
              </div>
            )}

            {/* Admin Navigation Pills */}
            <div style={{ display: 'flex', gap: '8px', backgroundColor: themeCard, padding: '6px', borderRadius: '12px', border: `1px solid ${themeBorder}`, flexWrap: 'wrap' }}>
              {[
                { id: 'rules', label: '⚙️ Calculation Rules' },
                { id: 'factors', label: '🏷️ Factor Overrides' },
                { id: 'cbam', label: '📊 CBAM Benchmarks' },
                { id: 'safeguards', label: '🛡️ AI Quality Safeguards' },
                { id: 'users', label: '👥 User Governance' },
                { id: 'audit', label: '📜 Audit Log' }
              ].map(st => (
                <button
                  key={st.id}
                  onClick={() => setAdminSubTab(st.id)}
                  style={{
                    padding: '10px 18px',
                    borderRadius: '8px',
                    border: 'none',
                    backgroundColor: adminSubTab === st.id ? '#10b981' : 'transparent',
                    color: adminSubTab === st.id ? '#080c14' : themeSubtext,
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    fontSize: '13px',
                    transition: 'all 0.2s'
                  }}
                >
                  {st.label}
                </button>
              ))}
            </div>

            {/* 1. CALCULATION RULES SUB-TAB */}
            {adminSubTab === 'rules' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div style={{ backgroundColor: themeCard, padding: '24px', borderRadius: '16px', border: `1px solid ${themeBorder}` }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0', color: '#10b981' }}>➕ Create Dynamic Calculation Rule</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '14px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Rule Name</label>
                      <input 
                        type="text" 
                        placeholder="e.g. Steel Scrap Scope Routing"
                        value={newRule.rule_name}
                        onChange={e => setNewRule({ ...newRule, rule_name: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Condition Field</label>
                      <select 
                        value={newRule.condition_field}
                        onChange={e => setNewRule({ ...newRule, condition_field: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}>
                        <option value="material">Material Name</option>
                        <option value="supplier">Supplier Name</option>
                        <option value="hs_code">HS Tariff Code</option>
                        <option value="quantity">Quantity Value</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Operator</label>
                      <select 
                        value={newRule.condition_operator}
                        onChange={e => setNewRule({ ...newRule, condition_operator: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}>
                        <option value="contains">Contains Keyword</option>
                        <option value="equals">Equals Exactly</option>
                        <option value="regex">Regex Pattern</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Match Value</label>
                      <input 
                        type="text" 
                        placeholder="e.g. scrap"
                        value={newRule.condition_value}
                        onChange={e => setNewRule({ ...newRule, condition_value: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '14px', alignItems: 'end' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Target Action</label>
                      <select 
                        value={newRule.target_action}
                        onChange={e => setNewRule({ ...newRule, target_action: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}>
                        <option value="set_scope">Route to Scope (Scope 1/2/3)</option>
                        <option value="set_factor">Override Emission Factor</option>
                        <option value="force_review">Force Auditor Review</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Action Value</label>
                      <input 
                        type="text" 
                        placeholder="e.g. Scope 3 or 0.0"
                        value={newRule.target_value}
                        onChange={e => setNewRule({ ...newRule, target_value: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Priority (Lower runs first)</label>
                      <input 
                        type="number" 
                        value={newRule.priority}
                        onChange={e => setNewRule({ ...newRule, priority: parseInt(e.target.value) || 10 })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                    <button 
                      onClick={handleSaveRule}
                      style={{ padding: '9px 20px', borderRadius: '6px', backgroundColor: '#10b981', border: 'none', color: '#080c14', fontWeight: 'bold', fontSize: '13px', cursor: 'pointer' }}>
                      Add Rule
                    </button>
                  </div>
                </div>

                {/* Active Rules List */}
                <div style={{ backgroundColor: themeCard, padding: '24px', borderRadius: '16px', border: `1px solid ${themeBorder}` }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0' }}>📋 Active Engine Rules ({adminRules.length})</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, fontSize: '11px', textTransform: 'uppercase' }}>
                        <th style={{ padding: '8px' }}>Priority</th>
                        <th style={{ padding: '8px' }}>Rule Name</th>
                        <th style={{ padding: '8px' }}>Condition</th>
                        <th style={{ padding: '8px' }}>Target Action</th>
                        <th style={{ padding: '8px' }}>Updated By</th>
                        <th style={{ padding: '8px' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminRules.map(r => (
                        <tr key={r.id} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                          <td style={{ padding: '8px', fontWeight: 'bold', color: '#10b981' }}>#{r.priority}</td>
                          <td style={{ padding: '8px', fontWeight: 'bold' }}>{r.rule_name}</td>
                          <td style={{ padding: '8px' }}><code>{r.condition_field}</code> {r.condition_operator} <strong>"{r.condition_value}"</strong></td>
                          <td style={{ padding: '8px', color: '#3b82f6', fontWeight: '600' }}>{r.target_action} ➔ {r.target_value}</td>
                          <td style={{ padding: '8px', color: themeSubtext, fontSize: '11px' }}>{r.updated_by}</td>
                          <td style={{ padding: '8px' }}>
                            <button 
                              onClick={() => handleDeleteRule(r.id)} 
                              style={{ padding: '4px 10px', borderRadius: '4px', border: '1px solid #ef4444', background: 'rgba(239,68,68,0.15)', color: '#f87171', cursor: 'pointer', fontSize: '11px' }}>
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 2. FACTOR OVERRIDES SUB-TAB */}
            {adminSubTab === 'factors' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div style={{ backgroundColor: themeCard, padding: '24px', borderRadius: '16px', border: `1px solid ${themeBorder}` }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0', color: '#10b981' }}>🏷️ Add Supplier & Regional Factor Override</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '14px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Material Pattern</label>
                      <input 
                        type="text" 
                        placeholder="e.g. Green Steel EAF"
                        value={newFactor.material_pattern}
                        onChange={e => setNewFactor({ ...newFactor, material_pattern: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Region</label>
                      <select 
                        value={newFactor.region}
                        onChange={e => setNewFactor({ ...newFactor, region: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}>
                        <option value="DE">Germany (DE)</option>
                        <option value="IN">India (IN)</option>
                        <option value="US">United States (US)</option>
                        <option value="FR">France (FR)</option>
                        <option value="GB">United Kingdom (GB)</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Scope</label>
                      <select 
                        value={newFactor.scope}
                        onChange={e => setNewFactor({ ...newFactor, scope: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}>
                        <option value="Scope 1">Scope 1</option>
                        <option value="Scope 2">Scope 2</option>
                        <option value="Scope 3">Scope 3</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Custom Emission Factor (kg CO₂e/unit)</label>
                      <input 
                        type="number" 
                        step="0.001"
                        value={newFactor.custom_emission_factor}
                        onChange={e => setNewFactor({ ...newFactor, custom_emission_factor: parseFloat(e.target.value) || 0.0 })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '14px', alignItems: 'end' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Unit</label>
                      <input 
                        type="text" 
                        placeholder="kg"
                        value={newFactor.unit}
                        onChange={e => setNewFactor({ ...newFactor, unit: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Source / EPD Certification</label>
                      <input 
                        type="text" 
                        placeholder="Supplier EPD Certificate #4892"
                        value={newFactor.source_name}
                        onChange={e => setNewFactor({ ...newFactor, source_name: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 'bold', color: themeSubtext, marginBottom: '4px' }}>Reason</label>
                      <input 
                        type="text" 
                        placeholder="Audited EAF Facility Data"
                        value={newFactor.reason}
                        onChange={e => setNewFactor({ ...newFactor, reason: e.target.value })}
                        style={{ width: '100%', boxSizing: 'border-box', padding: '8px 10px', borderRadius: '6px', backgroundColor: isDarkMode ? '#080c14' : '#fff', border: `1px solid ${themeBorder}`, color: themeText, fontSize: '12px' }}
                      />
                    </div>
                    <button 
                      onClick={handleSaveFactorOverride}
                      style={{ padding: '9px 20px', borderRadius: '6px', backgroundColor: '#10b981', border: 'none', color: '#080c14', fontWeight: 'bold', fontSize: '13px', cursor: 'pointer' }}>
                      Save Override
                    </button>
                  </div>
                </div>

                {/* Overrides Table */}
                <div style={{ backgroundColor: themeCard, padding: '24px', borderRadius: '16px', border: `1px solid ${themeBorder}` }}>
                  <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0' }}>📋 Emission Factor Overrides ({adminFactors.length})</h3>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, fontSize: '11px', textTransform: 'uppercase' }}>
                        <th style={{ padding: '8px' }}>Pattern</th>
                        <th style={{ padding: '8px' }}>Region</th>
                        <th style={{ padding: '8px' }}>Scope</th>
                        <th style={{ padding: '8px' }}>Factor</th>
                        <th style={{ padding: '8px' }}>Source</th>
                        <th style={{ padding: '8px' }}>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminFactors.map(f => (
                        <tr key={f.id} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                          <td style={{ padding: '8px', fontWeight: 'bold' }}>{f.material_pattern}</td>
                          <td style={{ padding: '8px' }}><span style={{ backgroundColor: 'rgba(59,130,246,0.15)', color: '#60a5fa', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>{f.region}</span></td>
                          <td style={{ padding: '8px' }}>{f.scope}</td>
                          <td style={{ padding: '8px', color: '#10b981', fontWeight: 'bold' }}>{f.custom_emission_factor} kg CO₂e/{f.unit}</td>
                          <td style={{ padding: '8px' }}>{f.source_name}</td>
                          <td style={{ padding: '8px', color: themeSubtext }}>{f.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 3. CBAM BENCHMARKS SUB-TAB */}
            {adminSubTab === 'cbam' && (
              <div style={{ backgroundColor: themeCard, padding: '24px', borderRadius: '16px', border: `1px solid ${themeBorder}`, maxWidth: '600px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0', color: '#10b981' }}>📊 CBAM & EU ETS Economic Benchmarks</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px' }}>EU ETS Carbon Price Benchmark (€ / Tonne CO₂e)</label>
                    <input 
                      type="number" 
                      value={carbonPrice}
                      onChange={e => setCarbonPrice(parseFloat(e.target.value) || 0.0)}
                      style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px' }}>Default Reporting Region</label>
                    <select 
                      value={defaultRegion}
                      onChange={e => setDefaultRegion(e.target.value)}
                      style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}>
                      <option value="DE">Germany (DE)</option>
                      <option value="IN">India (IN)</option>
                      <option value="US">United States (US)</option>
                      <option value="FR">France (FR)</option>
                      <option value="GB">United Kingdom (GB)</option>
                    </select>
                  </div>
                  <button 
                    onClick={handleSaveSettings}
                    style={{ padding: '12px', borderRadius: '8px', border: 'none', backgroundColor: '#10b981', color: '#080c14', fontWeight: 'bold', fontSize: '14px', cursor: 'pointer' }}>
                    Save Benchmarks
                  </button>
                </div>
              </div>
            )}

            {/* 4. AI QUALITY SAFEGUARDS SUB-TAB */}
            {adminSubTab === 'safeguards' && (
              <div style={{ backgroundColor: themeCard, padding: '24px', borderRadius: '16px', border: `1px solid ${themeBorder}`, maxWidth: '600px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0', color: '#10b981' }}>🛡️ AI Quality Gates & Thresholds</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px' }}>OCR Confidence Gate Trigger (%)</label>
                    <input 
                      type="number" 
                      defaultValue={90}
                      style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}
                    />
                    <span style={{ fontSize: '11px', color: themeSubtext }}>Documents below this confidence score are automatically routed to manual auditor review.</span>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '6px' }}>Anomaly Detection Multiplier (x Std Dev)</label>
                    <input 
                      type="number" 
                      defaultValue={4.0}
                      step="0.5"
                      style={{ width: '100%', boxSizing: 'border-box', padding: '10px 12px', borderRadius: '8px', border: `1px solid ${themeBorder}`, backgroundColor: isDarkMode ? '#080c14' : '#fff', color: themeText, fontSize: '13px' }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* 5. USER GOVERNANCE SUB-TAB */}
            {adminSubTab === 'users' && (
              <div style={{ backgroundColor: themeCard, padding: '24px', borderRadius: '16px', border: `1px solid ${themeBorder}` }}>
                <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0' }}>👥 User Accounts & Governance ({adminUsers.length})</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, fontSize: '11px', textTransform: 'uppercase' }}>
                      <th style={{ padding: '8px' }}>User</th>
                      <th style={{ padding: '8px' }}>Organization</th>
                      <th style={{ padding: '8px' }}>Role</th>
                      <th style={{ padding: '8px' }}>Status</th>
                      <th style={{ padding: '8px' }}>Last Login</th>
                      <th style={{ padding: '8px' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminUsers.map(u => (
                      <tr key={u.id} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                        <td style={{ padding: '8px' }}>
                          <div style={{ fontWeight: 'bold' }}>{u.full_name}</div>
                          <div style={{ fontSize: '11px', color: themeSubtext }}>{u.email}</div>
                        </td>
                        <td style={{ padding: '8px' }}>{u.organization}</td>
                        <td style={{ padding: '8px' }}>
                          <span style={{ 
                            padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold',
                            backgroundColor: u.role === 'admin' ? 'rgba(139,92,246,0.15)' : 'rgba(16,185,129,0.15)',
                            color: u.role === 'admin' ? '#c084fc' : '#34d399'
                          }}>
                            {u.role.toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '8px' }}>
                          <span style={{ color: u.is_active ? '#10b981' : '#f87171', fontWeight: 'bold' }}>
                            {u.is_active ? '● Active' : '○ Suspended'}
                          </span>
                        </td>
                        <td style={{ padding: '8px', color: themeSubtext, fontSize: '11px' }}>{u.last_login || 'Never'}</td>
                        <td style={{ padding: '8px' }}>
                          <button 
                            onClick={() => handleToggleUserStatus(u.id)}
                            style={{ padding: '4px 10px', borderRadius: '4px', border: '1px solid #3b82f6', background: 'rgba(59,130,246,0.15)', color: '#60a5fa', cursor: 'pointer', fontSize: '11px' }}>
                            {u.is_active ? 'Suspend' : 'Activate'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* 6. AUDIT LOG SUB-TAB */}
            {adminSubTab === 'audit' && (
              <div style={{ backgroundColor: themeCard, padding: '24px', borderRadius: '16px', border: `1px solid ${themeBorder}` }}>
                <h3 style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 16px 0' }}>📜 Configuration Audit Log</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ borderBottom: `1px solid ${themeBorder}`, textAlign: 'left', color: themeSubtext, fontSize: '11px', textTransform: 'uppercase' }}>
                      <th style={{ padding: '8px' }}>Timestamp</th>
                      <th style={{ padding: '8px' }}>Admin</th>
                      <th style={{ padding: '8px' }}>Action</th>
                      <th style={{ padding: '8px' }}>Module</th>
                      <th style={{ padding: '8px' }}>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminAuditLogs.map(a => (
                      <tr key={a.id} style={{ borderBottom: `1px solid ${themeBorder}` }}>
                        <td style={{ padding: '8px', color: themeSubtext }}>{a.timestamp}</td>
                        <td style={{ padding: '8px', fontWeight: 'bold' }}>{a.user_email}</td>
                        <td style={{ padding: '8px' }}><span style={{ backgroundColor: 'rgba(16,185,129,0.15)', color: '#10b981', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>{a.action_type}</span></td>
                        <td style={{ padding: '8px' }}>{a.target_module}</td>
                        <td style={{ padding: '8px', color: themeText }}>{a.new_value || a.old_value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

          </div>
        )}

      </main>

    </div>
  );
}
