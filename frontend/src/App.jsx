import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import UploadPanel from './components/UploadPanel';
import Leaderboard from './components/Leaderboard';
import RecruiterCard from './components/RecruiterCard';
import { getJobs, getLeaderboard } from './services/api';
import { Briefcase, AlertCircle, Cpu, ShieldAlert, Clock, GraduationCap, MapPin } from 'lucide-react';

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [filterDisqualified, setFilterDisqualified] = useState(true);

  const [loadingJobs, setLoadingJobs] = useState(false);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [error, setError] = useState('');

  // 1. Initial jobs fetch
  const fetchJobs = async (selectNewJobId = null) => {
    setLoadingJobs(true);
    try {
      const data = await getJobs();
      setJobs(data);
      if (data.length > 0) {
        if (selectNewJobId) {
          const matched = data.find(j => j.id === selectNewJobId);
          setSelectedJob(matched || data[0]);
        } else if (!selectedJob) {
          setSelectedJob(data[0]);
        } else {
          // Sync selected job data in case it refreshed
          const current = data.find(j => j.id === selectedJob.id);
          if (current) setSelectedJob(current);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to retrieve jobs list from server.');
    } finally {
      setLoadingJobs(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  // 2. Fetch Leaderboard when active job or filter changes
  const fetchCandidates = async () => {
    if (!selectedJob) return;
    setLoadingCandidates(true);
    try {
      const data = await getLeaderboard(selectedJob.id, filterDisqualified);
      setCandidates(data);
    } catch (err) {
      console.error('Failed to retrieve candidates:', err);
    } finally {
      setLoadingCandidates(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
    // Close candidate detail panel when swapping roles
    setSelectedCandidate(null);
  }, [selectedJob, filterDisqualified]);

  // Callback when a new job is successfully extracted
  const handleJobCreated = (newJob) => {
    fetchJobs(newJob.id);
  };

  // Callback when an upload evaluation completes
  const handleUploadSuccess = () => {
    fetchCandidates();
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-105 overflow-hidden font-sans antialiased">
      {/* Sidebar - Positions List */}
      <Sidebar
        jobs={jobs}
        selectedJob={selectedJob}
        onSelectJob={setSelectedJob}
        onJobCreated={handleJobCreated}
      />

      {/* Main Panel Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Main Header */}
        <header className="px-8 py-5 border-b border-slate-800 bg-slate-900/10 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-black text-white tracking-tight">TalentLens Console</h1>
            <p className="text-xs text-slate-500 mt-0.5">Evaluate applicant resumes, flag keyword spoofing, and explore AI fits.</p>
          </div>
          
          <div className="flex items-center space-x-2 text-xs text-slate-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>API Online</span>
          </div>
        </header>

        {/* Workspace Body */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
          {error && (
            <div className="p-4 bg-red-950/40 border border-red-500/20 rounded-2xl flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-red-200">Server Connection Error</h4>
                <p className="text-xs text-red-350 mt-1">{error}</p>
              </div>
            </div>
          )}

          {selectedJob ? (
            <>
              {/* Active Position Requirements Overview */}
              <div className="bg-gradient-to-r from-brand-950/10 to-indigo-950/10 border border-slate-800/80 rounded-2xl p-6 shadow-lg relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/5 rounded-full blur-3xl -mr-16 -mt-16 group-hover:bg-brand-500/10 transition-colors duration-500"></div>
                <div className="relative z-10 flex flex-col md:flex-row md:items-start justify-between gap-6">
                  <div className="space-y-2.5 max-w-2xl">
                    <div className="flex items-center space-x-2.5">
                      <div className="px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider rounded bg-indigo-500/10 border border-indigo-500/35 text-indigo-400">
                        Active Job Context
                      </div>
                      {selectedJob.department && (
                        <span className="text-xs text-slate-500">• {selectedJob.department}</span>
                      )}
                    </div>
                    <h2 className="text-lg font-black text-white">{selectedJob.title}</h2>
                    <p className="text-xs text-slate-400 leading-relaxed max-w-xl line-clamp-3">
                      {selectedJob.description}
                    </p>
                  </div>

                  {/* Requirements Metrics Card */}
                  <div className="bg-slate-950/50 border border-slate-850 p-4 rounded-xl space-y-3 shrink-0 w-72">
                    <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Evaluation Benchmarks</div>
                    
                    <div className="space-y-2 text-xs">
                      {selectedJob.experience_required_years !== null && (
                        <div className="flex items-center space-x-2.5 text-slate-300">
                          <Clock className="w-4 h-4 text-brand-400 shrink-0" />
                          <span>Experience: <strong className="text-white">{selectedJob.experience_required_years}+ years</strong></span>
                        </div>
                      )}

                      {selectedJob.education_required && (
                        <div className="flex items-center space-x-2.5 text-slate-300">
                          <GraduationCap className="w-4 h-4 text-brand-400 shrink-0" />
                          <span className="truncate">Degree: <strong className="text-white" title={selectedJob.education_required}>{selectedJob.education_required}</strong></span>
                        </div>
                      )}

                      {selectedJob.location && (
                        <div className="flex items-center space-x-2.5 text-slate-300">
                          <MapPin className="w-4 h-4 text-brand-400 shrink-0" />
                          <span>Location: <strong className="text-white">{selectedJob.location}</strong></span>
                        </div>
                      )}
                    </div>

                    {selectedJob.skills_required && selectedJob.skills_required.length > 0 && (
                      <div className="pt-2 border-t border-slate-850">
                        <span className="text-[9px] font-bold text-slate-500 uppercase block mb-1">Target Skills</span>
                        <div className="flex flex-wrap gap-1">
                          {selectedJob.skills_required.slice(0, 5).map((skill, index) => (
                            <span key={index} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-900 border border-slate-800 text-slate-300">
                              {skill}
                            </span>
                          ))}
                          {selectedJob.skills_required.length > 5 && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-900 border border-slate-800 text-slate-500">
                              +{selectedJob.skills_required.length - 5} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Upload candidate dataset section */}
              <UploadPanel
                selectedJob={selectedJob}
                onUploadSuccess={handleUploadSuccess}
              />

              {/* Rankings leaderboard dashboard */}
              <Leaderboard
                candidates={candidates}
                filterDisqualified={filterDisqualified}
                onToggleFilterDisqualified={() => setFilterDisqualified(!filterDisqualified)}
                onSelectCandidate={setSelectedCandidate}
                selectedCandidate={selectedCandidate}
              />
            </>
          ) : (
            <div className="h-96 border border-dashed border-slate-800 rounded-2xl bg-slate-900/10 flex flex-col items-center justify-center text-center p-8">
              <div className="p-4 bg-slate-900 rounded-full border border-slate-800 text-slate-500 mb-4 animate-pulse">
                <Briefcase className="w-8 h-8" />
              </div>
              <h3 className="text-md font-bold text-white">No Position Selected</h3>
              <p className="text-xs text-slate-500 mt-2 max-w-sm">
                Select a position from the sidebar panel or create a new job description to begin uploading candidates and calculating rankings.
              </p>
            </div>
          )}
        </div>

        {/* Detailed Recruiter Analysis Side Drawer */}
        {selectedCandidate && (
          <>
            {/* Backdrop cover overlay */}
            <div
              className="fixed inset-0 z-30 bg-slate-950/60 backdrop-blur-xs transition-opacity duration-300"
              onClick={() => setSelectedCandidate(null)}
            ></div>
            <RecruiterCard
              jobId={selectedJob.id}
              candidateSummary={selectedCandidate}
              onClose={() => setSelectedCandidate(null)}
            />
          </>
        )}
      </div>
    </div>
  );
}
