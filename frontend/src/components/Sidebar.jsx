import React, { useState } from 'react';
import { Briefcase, Plus, MapPin, Clock, GraduationCap, X, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import { createJob } from '../services/api';

export default function Sidebar({ jobs, selectedJob, onSelectJob, onJobCreated }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      setError('Please fill in both the job title and the raw description.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const newJob = await createJob(title, description);
      setTitle('');
      setDescription('');
      setIsModalOpen(false);
      if (onJobCreated) {
        onJobCreated(newJob);
      }
    } catch (err) {
      setError(err.message || 'Failed to analyze job description.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-80 border-r border-slate-800 bg-slate-950 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-tr from-brand-600 to-indigo-600 rounded-xl shadow-lg shadow-brand-500/20">
            <Briefcase className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight leading-none">TalentLens</h1>
            <span className="text-xs text-slate-500 font-medium">JD Analysis & Rankings</span>
          </div>
        </div>
      </div>

      {/* Action Button */}
      <div className="p-4">
        <button
          onClick={() => setIsModalOpen(true)}
          className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-medium px-4 py-3 rounded-xl shadow-lg shadow-brand-500/10 hover:shadow-brand-500/20 transition-all duration-300 transform hover:-translate-y-0.5 active:translate-y-0 text-sm group"
        >
          <Plus className="w-4 h-4 transition-transform group-hover:rotate-90 duration-300" />
          <span>New Job Description</span>
        </button>
      </div>

      {/* Job List */}
      <div className="flex-1 overflow-y-auto px-4 pb-6 space-y-3 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
        <div className="text-xs font-semibold text-slate-500 px-2 uppercase tracking-wider mb-2">
          Active Positions ({jobs.length})
        </div>
        {jobs.length === 0 ? (
          <div className="text-center py-8 px-4 rounded-xl border border-dashed border-slate-800 bg-slate-900/20">
            <Briefcase className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
            <p className="text-xs text-slate-400">No positions created yet.</p>
            <p className="text-[10px] text-slate-500 mt-1">Create one to begin candidate matching.</p>
          </div>
        ) : (
          jobs.map((job) => {
            const isSelected = selectedJob && selectedJob.id === job.id;
            return (
              <button
                key={job.id}
                onClick={() => onSelectJob(job)}
                className={`w-full text-left p-4 rounded-xl transition-all duration-300 border text-sm group ${
                  isSelected
                    ? 'bg-slate-900/60 border-brand-500/40 shadow-md shadow-brand-950/20'
                    : 'bg-slate-900/20 border-slate-800/40 hover:bg-slate-900/40 hover:border-slate-850'
                }`}
              >
                <div className="font-semibold text-slate-200 group-hover:text-white transition-colors duration-200">
                  {job.title}
                </div>
                {job.department && (
                  <div className="text-xs text-brand-400 font-medium mt-1">
                    {job.department}
                  </div>
                )}
                
                {/* Meta details */}
                <div className="mt-3 space-y-1.5 text-xs text-slate-400">
                  {job.experience_required_years && (
                    <div className="flex items-center space-x-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span>{job.experience_required_years}+ years exp</span>
                    </div>
                  )}
                  {job.education_required && (
                    <div className="flex items-center space-x-1.5 truncate">
                      <GraduationCap className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span className="truncate">{job.education_required}</span>
                    </div>
                  )}
                  {job.location && (
                    <div className="flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span>{job.location}</span>
                    </div>
                  )}
                </div>

                {/* Skills tags */}
                {job.skills_required && job.skills_required.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {job.skills_required.slice(0, 3).map((skill, index) => (
                      <span
                        key={index}
                        className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800/80 text-slate-300 font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                    {job.skills_required.length > 3 && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800/80 text-slate-400">
                        +{job.skills_required.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })
        )}
      </div>

      {/* Modal Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-slide-up">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-850">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-brand-400" />
                <h2 className="text-md font-bold text-white">Create & Analyze Position</h2>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all duration-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {error && (
                <div className="p-3 bg-red-950/40 border border-red-500/25 rounded-xl flex items-start space-x-2.5">
                  <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-red-200 leading-normal">{error}</p>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Target Job Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Machine Learning Engineer"
                  disabled={loading}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:ring-1 focus:ring-brand-500/50 outline-none transition-all duration-200"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Raw Job Description Text
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows="8"
                  placeholder="Paste the target requirements, required education level, core responsibilities, and key disqualification keywords..."
                  disabled={loading}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:ring-1 focus:ring-brand-500/50 outline-none transition-all duration-200 resize-none font-sans"
                />
              </div>

              <div className="pt-2 border-t border-slate-850 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={loading}
                  className="px-4 py-2 text-sm text-slate-450 hover:text-white font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center space-x-2 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-medium px-5 py-2.5 rounded-xl shadow-lg shadow-brand-500/10 hover:shadow-brand-500/20 disabled:opacity-50 transition-all duration-300"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Extracting with LLM...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Analyze JD</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
