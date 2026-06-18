import React, { useState, useEffect } from 'react';
import { X, Mail, Phone, User, Sparkles, Award, BookOpen, Briefcase, Globe, ShieldAlert, CheckCircle2, HelpCircle, Activity, FileText } from 'lucide-react';
import { getCandidateDetails } from '../services/api';

export default function RecruiterCard({ jobId, candidateSummary, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!jobId || !candidateSummary) return;

    const fetchDetails = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getCandidateDetails(jobId, candidateSummary.candidate_id);
        setDetails(data);
      } catch (err) {
        setError(err.message || 'Failed to fetch candidate details.');
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [jobId, candidateSummary]);

  if (!candidateSummary) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-[500px] bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full overflow-hidden animate-slide-left">
      {/* Header */}
      <div className="p-6 border-b border-slate-850 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-brand-500/10 border border-brand-500/35 flex items-center justify-center text-brand-400">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-tight">{candidateSummary.name}</h2>
            <span className="text-[10px] text-slate-500 font-mono">ID: {candidateSummary.candidate_id}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all duration-200"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main Drawer Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-brand-500/20 border-t-brand-500 animate-spin"></div>
            <span className="text-xs text-slate-500 font-medium">Analyzing resume credentials...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-950/35 border border-red-500/25 rounded-xl flex items-start space-x-2.5">
            <ShieldAlert className="w-5 h-5 text-red-400 shrink-0" />
            <div className="text-xs text-red-200">{error}</div>
          </div>
        ) : details ? (
          <>
            {/* Contact details */}
            <div className="grid grid-cols-2 gap-3 bg-slate-950/40 border border-slate-850 rounded-xl p-4 text-xs text-slate-400">
              <div className="flex items-center space-x-2.5 min-w-0">
                <Mail className="w-4 h-4 text-slate-500 shrink-0" />
                <span className="truncate">{details.email || 'N/A'}</span>
              </div>
              <div className="flex items-center space-x-2.5 min-w-0">
                <Phone className="w-4 h-4 text-slate-500 shrink-0" />
                <span>{details.phone || 'N/A'}</span>
              </div>
            </div>

            {/* Overall Composite Score Visualizer */}
            <div className="border border-slate-850 rounded-xl p-5 bg-gradient-to-r from-slate-950/20 to-slate-950/40 flex items-center justify-between">
              <div className="space-y-1">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Composite Match Score</h3>
                <p className="text-xs text-slate-500">Aggregated match index against core JD requisites.</p>
                {details.is_disqualified ? (
                  <span className="inline-flex items-center space-x-1 mt-2 text-[10px] font-bold text-red-400 bg-red-950/40 border border-red-500/20 px-2 py-0.5 rounded">
                    <ShieldAlert className="w-3 h-3 shrink-0" />
                    <span>Disqualified by Filter</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center space-x-1 mt-2 text-[10px] font-bold text-emerald-400 bg-emerald-950/40 border border-emerald-500/20 px-2 py-0.5 rounded">
                    <CheckCircle2 className="w-3 h-3 shrink-0" />
                    <span>Qualified Profile</span>
                  </span>
                )}
              </div>
              
              {/* Circular SVG Score Chart */}
              <div className="relative w-20 h-20 shrink-0">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-slate-800"
                    strokeWidth="3.5"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <path
                    className={details.is_disqualified ? 'text-red-500' : details.final_score >= 75 ? 'text-emerald-500' : 'text-brand-500'}
                    strokeWidth="3.5"
                    strokeDasharray={`${details.final_score}, 100`}
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                  <span className="text-sm font-black text-white">{Math.round(details.final_score)}%</span>
                </div>
              </div>
            </div>

            {/* Grid of breakdowns */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950/20 border border-slate-850 p-4 rounded-xl space-y-1">
                <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <span>Skills Score</span>
                  <span className="text-slate-300 font-mono">{Math.round(details.skill_score)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-brand-500 h-full rounded-full" style={{ width: `${details.skill_score}%` }}></div>
                </div>
              </div>

              <div className="bg-slate-950/20 border border-slate-850 p-4 rounded-xl space-y-1">
                <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <span>Career Tenure</span>
                  <span className="text-slate-300 font-mono">{Math.round(details.career_score)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${details.career_score}%` }}></div>
                </div>
              </div>

              <div className="bg-slate-950/20 border border-slate-850 p-4 rounded-xl space-y-1">
                <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <span>Behavioral Index</span>
                  <span className="text-slate-300 font-mono">{Math.round(details.behavioral_score)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-teal-500 h-full rounded-full" style={{ width: `${details.behavioral_score}%` }}></div>
                </div>
              </div>

              <div className="bg-slate-950/20 border border-slate-850 p-4 rounded-xl space-y-1">
                <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <span>Education Tier</span>
                  <span className="text-slate-300 font-mono">{Math.round(details.education_score)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-orange-500 h-full rounded-full" style={{ width: `${details.education_score}%` }}></div>
                </div>
              </div>

              <div className="bg-slate-950/20 border border-slate-850 p-4 rounded-xl space-y-1 col-span-2">
                <div className="flex justify-between text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <span>Semantic Vector Match</span>
                  <span className="text-slate-300 font-mono">{Math.round(details.semantic_score)}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-pink-500 h-full rounded-full" style={{ width: `${details.semantic_score}%` }}></div>
                </div>
              </div>
            </div>

            {/* Honeypot Alert if triggered */}
            {details.honeypot_penalty > 0 && (
              <div className="bg-amber-950/30 border border-amber-500/20 p-4 rounded-xl flex items-start space-x-3">
                <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-amber-300">Keyword-Stuffing Detected (Honeypot Triggered)</h4>
                  <p className="text-[11px] text-amber-200/80 leading-normal mt-1">
                    This candidate's profile triggered penalty mechanisms for hidden keyword stuffing of target skills. Final score was penalized by <span className="font-bold text-amber-400">-{details.honeypot_penalty} points</span>.
                  </p>
                </div>
              </div>
            )}

            {/* Recruiter fit explanation card */}
            {details.fit_summary && (
              <div className="space-y-4 border-t border-slate-850 pt-5">
                <div className="flex items-center space-x-2">
                  <Sparkles className="w-4.5 h-4.5 text-brand-400" />
                  <h3 className="text-xs font-black text-slate-300 uppercase tracking-wider">Groq AI Recruiter Fit Evaluation</h3>
                </div>

                {/* Summary */}
                <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-4 space-y-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Fit Summary</span>
                  <p className="text-xs text-slate-300 leading-relaxed">{details.fit_summary}</p>
                </div>

                {/* Strengths */}
                {details.strengths && details.strengths.length > 0 && (
                  <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-4 space-y-2">
                    <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-wider block">Candidate Strengths</span>
                    <ul className="space-y-1.5">
                      {details.strengths.map((str, index) => (
                        <li key={index} className="flex items-start space-x-2 text-xs text-slate-300">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Concerns */}
                {details.concerns && details.concerns.length > 0 && (
                  <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-4 space-y-2">
                    <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider block">Areas of Concern / Gaps</span>
                    <ul className="space-y-1.5">
                      {details.concerns.map((con, index) => (
                        <li key={index} className="flex items-start space-x-2 text-xs text-slate-300">
                          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                          <span>{con}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Interview Questions */}
                {details.interview_questions && details.interview_questions.length > 0 && (
                  <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-4 space-y-2">
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block">Suggested Screening Questions</span>
                    <ul className="space-y-2">
                      {details.interview_questions.map((q, index) => (
                        <li key={index} className="flex items-start space-x-2 bg-slate-950/50 border border-slate-850 p-2.5 rounded-lg text-xs text-slate-200">
                          <HelpCircle className="w-4.5 h-4.5 text-indigo-400 shrink-0 mt-0.5" />
                          <span>{q}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Candidate Raw Profile Information */}
            <div className="space-y-4 border-t border-slate-850 pt-5">
              <div className="flex items-center space-x-2">
                <FileText className="w-4.5 h-4.5 text-slate-400" />
                <h3 className="text-xs font-black text-slate-300 uppercase tracking-wider">Resume History</h3>
              </div>

              {/* Bio Summary */}
              {details.summary && (
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Candidate Summary</span>
                  <p className="text-xs text-slate-400 leading-normal">{details.summary}</p>
                </div>
              )}

              {/* Skills Tags */}
              {details.skills && details.skills.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Candidate Skills</span>
                  <div className="flex flex-wrap gap-1">
                    {details.skills.map((s, index) => (
                      <span key={index} className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300 font-medium">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Work Experience */}
              {details.experience && details.experience.length > 0 && (
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Work Experience</span>
                  <div className="space-y-3 relative border-l border-slate-800 pl-3.5 ml-1.5">
                    {details.experience.map((exp, index) => (
                      <div key={index} className="relative text-xs space-y-0.5">
                        <div className="absolute -left-[20.5px] top-1 w-2.5 h-2.5 rounded-full border border-slate-850 bg-slate-900 flex items-center justify-center">
                          <Briefcase className="w-1.5 h-1.5 text-slate-500" />
                        </div>
                        <div className="font-bold text-slate-200">{exp.title}</div>
                        <div className="text-[11px] text-slate-450">{exp.company || 'N/A'} • {exp.location || 'N/A'}</div>
                        <div className="text-[10px] text-brand-400 font-medium">{exp.start_date || 'N/A'} - {exp.end_date || 'N/A'}</div>
                        {exp.description && (
                          <p className="text-[11px] text-slate-400 mt-1 leading-normal">{exp.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Education */}
              {details.education && details.education.length > 0 && (
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Education</span>
                  <div className="space-y-2">
                    {details.education.map((edu, index) => (
                      <div key={index} className="flex items-start space-x-2.5 bg-slate-950/30 border border-slate-850 p-3 rounded-lg text-xs">
                        <BookOpen className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                        <div className="space-y-0.5">
                          <div className="font-bold text-slate-200">{edu.degree || 'Degree'} in {edu.major || 'Major'}</div>
                          <div className="text-[11px] text-slate-400">{edu.school || 'School'}</div>
                          <div className="text-[10px] text-slate-500 font-semibold">{edu.graduation_date || 'N/A'}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Certifications */}
              {details.certifications && details.certifications.length > 0 && (
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Certifications</span>
                  <div className="flex flex-wrap gap-2">
                    {details.certifications.map((cert, index) => (
                      <span key={index} className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-950/50 border border-slate-850 text-xs text-slate-300">
                        <Award className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span>{cert.name || 'Certificate'}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Languages */}
              {details.languages && details.languages.length > 0 && (
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Languages</span>
                  <div className="flex flex-wrap gap-2">
                    {details.languages.map((lang, index) => (
                      <span key={index} className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-950/50 border border-slate-850 text-xs text-slate-350">
                        <Globe className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span>{lang}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
