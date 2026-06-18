import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, Settings, Play, CheckCircle2, AlertCircle, Loader2, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { uploadCandidates, getUploadStatus } from '../services/api';

export default function UploadPanel({ selectedJob, onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  // Advanced parameters
  const [batchSize, setBatchSize] = useState(100);
  const [retrieveK, setRetrieveK] = useState(100);
  const [explainTopN, setExplainTopN] = useState(10);
  const [limit, setLimit] = useState('');

  // Status and polling state
  const [statusState, setStatusState] = useState({
    status: 'idle',
    job_id: null,
    error_message: null,
    elapsed_time_sec: 0,
    last_run_timestamp: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Poll status from server if processing
  const fetchStatus = async () => {
    try {
      const data = await getUploadStatus();
      setStatusState(data);
      if (data.status !== 'processing') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        if (data.status === 'completed' && onUploadSuccess) {
          onUploadSuccess();
        }
      }
    } catch (err) {
      console.error('Error fetching pipeline status:', err);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchStatus();

    // Setup polling if server is in processing state
    pollIntervalRef.current = setInterval(fetchStatus, 2000);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Sync polling if status changes to processing
  useEffect(() => {
    if (statusState.status === 'processing') {
      if (!pollIntervalRef.current) {
        pollIntervalRef.current = setInterval(fetchStatus, 2000);
      }
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [statusState.status]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.jsonl') || droppedFile.name.endsWith('.txt')) {
        setFile(droppedFile);
        setError('');
      } else {
        setError('Only .jsonl format is accepted.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (selected.name.endsWith('.jsonl') || selected.name.endsWith('.txt')) {
        setFile(selected);
        setError('');
      } else {
        setError('Only .jsonl format is accepted.');
      }
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a candidate profiles dataset file.');
      return;
    }
    if (!selectedJob) {
      setError('Please select a position from the left sidebar first.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const options = {
        batchSize,
        retrieveK,
        explainTopN,
        limit: limit ? parseInt(limit, 10) : null
      };
      
      const response = await uploadCandidates(selectedJob.id, file, options);
      setFile(null);
      // Trigger status check immediately
      fetchStatus();
    } catch (err) {
      setError(err.message || 'Failed to trigger candidate rankings pipeline.');
    } finally {
      setLoading(false);
    }
  };

  const isProcessing = statusState.status === 'processing';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-850 pb-4">
        <div>
          <h2 className="text-md font-bold text-white tracking-tight">Evaluate Candidates Dataset</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {selectedJob 
              ? `Ingesting dataset for "${selectedJob.title}"` 
              : 'Select a position from the sidebar to start uploading candidates.'}
          </p>
        </div>
        
        {/* Settings Toggle */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className={`flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all duration-300 ${
            showSettings 
              ? 'bg-brand-500/10 border-brand-500/30 text-brand-400' 
              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <Settings className="w-3.5 h-3.5" />
          <span>Advanced Tuning</span>
          {showSettings ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {error && (
        <div className="p-3.5 bg-red-950/40 border border-red-500/20 rounded-xl flex items-start space-x-2.5">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div className="text-xs text-red-200 leading-normal">{error}</div>
        </div>
      )}

      {/* Advanced Settings Drawer */}
      {showSettings && (
        <div className="bg-slate-950/50 border border-slate-850 rounded-xl p-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 animate-slide-down">
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Batch Ingestion Size
            </label>
            <input
              type="number"
              min="1"
              value={batchSize}
              onChange={(e) => setBatchSize(parseInt(e.target.value) || 1)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:border-brand-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Semantic Filter (Top-K)
            </label>
            <input
              type="number"
              min="1"
              value={retrieveK}
              onChange={(e) => setRetrieveK(parseInt(e.target.value) || 1)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:border-brand-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Groq LLM Explanations (Top-N)
            </label>
            <input
              type="number"
              min="0"
              value={explainTopN}
              onChange={(e) => setExplainTopN(parseInt(e.target.value) || 0)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:border-brand-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Limit Candidate Scope
            </label>
            <input
              type="number"
              min="1"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              placeholder="e.g. 500 (Optional)"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:border-brand-500 outline-none"
            />
          </div>
        </div>
      )}

      {/* Main Upload Dropzone / Progress Status */}
      {isProcessing ? (
        <div className="bg-slate-950/60 border border-brand-500/25 rounded-2xl p-8 flex flex-col items-center justify-center text-center space-y-4">
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-brand-500/20 blur-md animate-pulse"></div>
            <div className="relative p-4 bg-brand-500/10 border border-brand-500/30 rounded-full">
              <Loader2 className="w-8 h-8 text-brand-400 animate-spin" />
            </div>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Pipeline Execution In Progress</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md">
              The engine is streaming candidate records, calculating composite semantic similarities, detecting honeypot keyword-stuffing, and generating recruiter fits using Groq AI.
            </p>
          </div>
          
          <div className="flex items-center space-x-6 text-xs text-slate-400 pt-2">
            <div>
              <span className="text-[10px] font-semibold text-slate-500 block uppercase">Elapsed Time</span>
              <span className="font-mono text-white text-sm font-semibold">{statusState.elapsed_time_sec}s</span>
            </div>
            <div className="border-l border-slate-800 h-6"></div>
            <div>
              <span className="text-[10px] font-semibold text-slate-500 block uppercase">Job Context ID</span>
              <span className="text-white text-sm font-semibold">#{statusState.job_id}</span>
            </div>
          </div>
        </div>
      ) : (
        <form onSubmit={handleUploadSubmit} className="space-y-4">
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={triggerFileInput}
            className={`w-full min-h-[160px] border-2 border-dashed rounded-2xl flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-300 ${
              !selectedJob
                ? 'bg-slate-900/10 border-slate-850 opacity-40 cursor-not-allowed'
                : dragActive
                ? 'bg-brand-500/5 border-brand-500/50'
                : 'bg-slate-950/30 border-slate-800 hover:bg-slate-950/60 hover:border-slate-700'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              disabled={!selectedJob || loading}
              className="hidden"
              accept=".jsonl,.txt"
            />
            
            <UploadCloud className={`w-10 h-10 mb-3 transition-colors ${dragActive ? 'text-brand-400' : 'text-slate-500'}`} />
            
            {file ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-brand-400 flex items-center justify-center space-x-1.5">
                  <FileText className="w-4 h-4 shrink-0" />
                  <span>{file.name}</span>
                </p>
                <p className="text-[10px] text-slate-500">
                  {Math.round(file.size / 1024)} KB • Click or drag to swap file
                </p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-semibold text-slate-300">
                  Drag & drop candidates dataset
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Supports JSONL formatted candidate profiles dataset (.jsonl)
                </p>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            {/* Last Execution Info */}
            <div className="text-xs text-slate-500">
              {statusState.last_run_timestamp && (
                <div>
                  Last run: <span className="text-slate-400 font-medium">{statusState.last_run_timestamp}</span>
                  {statusState.status === 'failed' && (
                    <span className="text-red-400 font-medium ml-1.5"> (Failed: {statusState.error_message})</span>
                  )}
                  {statusState.status === 'completed' && (
                    <span className="text-emerald-500 font-medium ml-1.5"> (Completed in {statusState.elapsed_time_sec}s)</span>
                  )}
                </div>
              )}
            </div>

            {/* Run Button */}
            <button
              type="submit"
              disabled={!file || !selectedJob || loading}
              className="flex items-center space-x-2 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 disabled:from-slate-800 disabled:to-slate-800 text-white font-semibold px-6 py-2.5 rounded-xl shadow-lg hover:shadow-brand-500/10 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Triggering Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Run Evaluation Pipeline</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
