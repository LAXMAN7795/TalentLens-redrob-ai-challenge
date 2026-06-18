import React, { useState, useMemo } from 'react';
import { Search, Download, AlertTriangle, CheckCircle2, XCircle, Filter, BarChart3, TrendingUp, UserCheck, Trash2 } from 'lucide-react';

export default function Leaderboard({ candidates, filterDisqualified, onToggleFilterDisqualified, onSelectCandidate, selectedCandidate }) {
  const [searchTerm, setSearchTerm] = useState('');

  // 1. Client-side Search Filter
  const filteredCandidates = useMemo(() => {
    if (!searchTerm.trim()) return candidates;
    const term = searchTerm.toLowerCase();
    return candidates.filter(c => 
      c.name.toLowerCase().includes(term) || 
      c.candidate_id.toLowerCase().includes(term)
    );
  }, [candidates, searchTerm]);

  // 2. Metrics Summary
  const metrics = useMemo(() => {
    if (candidates.length === 0) return { avgScore: 0, total: 0, disqualified: 0, maxScore: 0 };
    let sum = 0;
    let max = 0;
    let disqCount = 0;
    candidates.forEach(c => {
      sum += c.final_score;
      if (c.final_score > max) max = c.final_score;
      if (c.is_disqualified) disqCount++;
    });
    return {
      avgScore: Math.round(sum / candidates.length),
      total: candidates.length,
      disqualified: disqCount,
      maxScore: Math.round(max)
    };
  }, [candidates]);

  // 3. Export CSV utility
  const handleExportCSV = () => {
    if (candidates.length === 0) return;
    
    // CSV headers
    const headers = [
      'Rank',
      'Candidate ID',
      'Name',
      'Final Score',
      'Skills Score',
      'Career Score',
      'Behavioral Score',
      'Education Score',
      'Semantic Score',
      'Honeypot Penalty',
      'Disqualified'
    ];

    // Map candidates to rows (ordered by Rank)
    const rows = candidates.map((c, index) => [
      index + 1,
      c.candidate_id,
      `"${c.name.replace(/"/g, '""')}"`,
      c.final_score.toFixed(2),
      c.skill_score.toFixed(2),
      c.career_score.toFixed(2),
      c.behavioral_score.toFixed(2),
      c.education_score.toFixed(2),
      c.semantic_score.toFixed(2),
      c.honeypot_penalty.toFixed(2),
      c.is_disqualified ? 'YES' : 'NO'
    ]);

    const csvContent = [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `talentlens_rankings_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // 4. Custom SVG Score Distribution Histogram (Zero-dependency charting)
  const scoreDistributionSvg = useMemo(() => {
    if (candidates.length === 0) return null;
    
    // Create 10 brackets from 0 to 100
    const brackets = Array(10).fill(0);
    candidates.forEach(c => {
      const idx = Math.min(Math.floor(c.final_score / 10), 9);
      if (idx >= 0) brackets[idx]++;
    });

    const maxBracketCount = Math.max(...brackets) || 1;
    const width = 500;
    const height = 80;
    const padding = 15;
    const barWidth = (width - padding * 2) / 10;

    return (
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
        {brackets.map((count, i) => {
          const barHeight = (count / maxBracketCount) * (height - padding * 2);
          const x = padding + i * barWidth;
          const y = height - padding - barHeight;
          const isHighlight = i >= 7; // Highlight 70+ (top fits)
          
          return (
            <g key={i} className="group/bar">
              <rect
                x={x + 2}
                y={y}
                width={barWidth - 4}
                height={barHeight}
                rx={3}
                className={`transition-all duration-300 ${
                  isHighlight 
                    ? 'fill-brand-500 hover:fill-brand-400' 
                    : 'fill-slate-800 hover:fill-slate-700'
                }`}
              />
              {/* Tooltip hint on hover */}
              <title>{`${i*10}-${(i+1)*10}%: ${count} candidates`}</title>
            </g>
          );
        })}
        {/* Baseline */}
        <line 
          x1={padding} 
          y1={height - padding} 
          x2={width - padding} 
          y2={height - padding} 
          className="stroke-slate-800" 
          strokeWidth={1} 
        />
        {/* Labels */}
        <text x={padding} y={height - 2} className="fill-slate-600 text-[9px] font-medium" textAnchor="start">0%</text>
        <text x={width / 2} y={height - 2} className="fill-slate-500 text-[9px] font-semibold" textAnchor="middle">Score Distribution</text>
        <text x={width - padding} y={height - 2} className="fill-slate-600 text-[9px] font-medium" textAnchor="end">100%</text>
      </svg>
    );
  }, [candidates]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6 flex-1 flex flex-col overflow-hidden">
      {/* Funnel Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-4 flex items-center space-x-3.5">
          <div className="p-3 bg-brand-500/10 border border-brand-500/20 rounded-xl text-brand-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Average Score</span>
            <span className="text-xl font-black text-white font-sans">{metrics.avgScore}%</span>
          </div>
        </div>

        <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-4 flex items-center space-x-3.5">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Total Evaluated</span>
            <span className="text-xl font-black text-white font-sans">{metrics.total}</span>
          </div>
        </div>

        <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-4 flex items-center space-x-3.5">
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
            <XCircle className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Disqualified</span>
            <span className="text-xl font-black text-white font-sans">{metrics.disqualified}</span>
          </div>
        </div>

        {/* Small inline distribution chart */}
        <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-3 flex flex-col justify-between h-[66px] overflow-hidden">
          {candidates.length > 0 ? (
            scoreDistributionSvg
          ) : (
            <div className="h-full flex items-center justify-center text-[10px] text-slate-600 font-medium">
              No distribution data
            </div>
          )}
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-t border-slate-850 pt-5">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search candidates by name or ID..."
            className="w-full bg-slate-950 border border-slate-800 focus:border-brand-500 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder:text-slate-600 focus:ring-1 focus:ring-brand-500/50 outline-none transition-all"
          />
        </div>

        <div className="flex items-center space-x-3">
          {/* Disqualification Filter */}
          <button
            onClick={onToggleFilterDisqualified}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl border text-xs font-semibold transition-all duration-300 ${
              filterDisqualified 
                ? 'bg-red-500/10 border-red-500/30 text-red-400' 
                : 'bg-slate-950 border-slate-850 text-slate-400 hover:text-white'
            }`}
          >
            <Filter className="w-3.5 h-3.5" />
            <span>{filterDisqualified ? 'Hiding Disqualified' : 'Showing All'}</span>
          </button>

          {/* Export CSV */}
          <button
            onClick={handleExportCSV}
            disabled={candidates.length === 0}
            className="flex items-center space-x-2 bg-slate-950 hover:bg-slate-850 text-slate-350 hover:text-white border border-slate-800 hover:border-slate-700 px-4 py-2 rounded-xl text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV Submission</span>
          </button>
        </div>
      </div>

      {/* Leaderboard Table Container */}
      <div className="flex-1 overflow-auto rounded-xl border border-slate-850 bg-slate-950/30">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="bg-slate-950/80 sticky top-0 z-10 border-b border-slate-850">
            <tr>
              <th className="px-5 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] w-14">Rank</th>
              <th className="px-5 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px]">Candidate Name</th>
              <th className="px-5 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] text-center w-24">Composite</th>
              <th className="px-4 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] text-center">Skills</th>
              <th className="px-4 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] text-center">Career</th>
              <th className="px-4 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] text-center">Behavioral</th>
              <th className="px-4 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] text-center">Education</th>
              <th className="px-4 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] text-center">Semantic</th>
              <th className="px-5 py-3.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] text-right w-28">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850/50">
            {filteredCandidates.length === 0 ? (
              <tr>
                <td colSpan="9" className="text-center py-12 text-slate-500">
                  {candidates.length === 0
                    ? 'No evaluation records available. Run the evaluation pipeline above.'
                    : 'No candidates matched your search criteria.'}
                </td>
              </tr>
            ) : (
              filteredCandidates.map((c, idx) => {
                const isDisq = c.is_disqualified;
                const hasHoneypot = c.honeypot_penalty > 0;
                const isSelected = selectedCandidate && selectedCandidate.candidate_id === c.candidate_id;

                return (
                  <tr
                    key={c.candidate_id}
                    onClick={() => onSelectCandidate(c)}
                    className={`cursor-pointer transition-all duration-200 ${
                      isSelected 
                        ? 'bg-brand-500/10 hover:bg-brand-500/15' 
                        : isDisq 
                        ? 'opacity-50 hover:bg-slate-900/10' 
                        : 'hover:bg-slate-900/30'
                    }`}
                  >
                    {/* Rank */}
                    <td className="px-5 py-3.5 font-semibold text-slate-400 font-mono text-center">
                      #{idx + 1}
                    </td>

                    {/* Candidate Identity */}
                    <td className="px-5 py-3.5">
                      <div className="font-bold text-slate-200 hover:text-white transition-colors duration-200">
                        {c.name}
                      </div>
                      <div className="text-[10px] font-mono text-slate-500 mt-0.5">
                        ID: {c.candidate_id}
                      </div>
                    </td>

                    {/* Composite Score */}
                    <td className="px-5 py-3.5 text-center">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-lg font-black text-xs font-sans border ${
                        isDisq 
                          ? 'bg-slate-900 border-slate-800 text-slate-500' 
                          : c.final_score >= 80 
                          ? 'bg-emerald-500/10 border-emerald-500/35 text-emerald-400 shadow-md shadow-emerald-950/20'
                          : c.final_score >= 60 
                          ? 'bg-brand-500/10 border-brand-500/35 text-brand-400' 
                          : 'bg-yellow-500/10 border-yellow-500/35 text-yellow-400'
                      }`}>
                        {Math.round(c.final_score)}%
                      </span>
                    </td>

                    {/* Score breakdowns */}
                    <td className="px-4 py-3.5 text-center font-semibold text-slate-300 font-mono">{Math.round(c.skill_score)}</td>
                    <td className="px-4 py-3.5 text-center font-semibold text-slate-300 font-mono">{Math.round(c.career_score)}</td>
                    <td className="px-4 py-3.5 text-center font-semibold text-slate-300 font-mono">{Math.round(c.behavioral_score)}</td>
                    <td className="px-4 py-3.5 text-center font-semibold text-slate-300 font-mono">{Math.round(c.education_score)}</td>
                    <td className="px-4 py-3.5 text-center font-semibold text-slate-300 font-mono">{Math.round(c.semantic_score)}</td>

                    {/* Status badges */}
                    <td className="px-5 py-3.5 text-right shrink-0">
                      <div className="flex items-center justify-end space-x-1.5">
                        {isDisq ? (
                          <span className="flex items-center space-x-1 text-[10px] font-bold text-red-400 bg-red-950/40 border border-red-500/20 px-2 py-0.5 rounded">
                            <XCircle className="w-3 h-3 shrink-0" />
                            <span>Disqualified</span>
                          </span>
                        ) : (
                          <span className="flex items-center space-x-1 text-[10px] font-bold text-emerald-400 bg-emerald-950/40 border border-emerald-500/20 px-2 py-0.5 rounded">
                            <CheckCircle2 className="w-3 h-3 shrink-0" />
                            <span>Qualified</span>
                          </span>
                        )}
                        {hasHoneypot && (
                          <span className="flex items-center space-x-1 text-[10px] font-bold text-yellow-400 bg-yellow-950/40 border border-yellow-500/20 px-1.5 py-0.5 rounded" title={`Honeypot keyword-stuffing penalized: -${c.honeypot_penalty} pts`}>
                            <AlertTriangle className="w-3 h-3 shrink-0" />
                            <span>Keyword Stuffed</span>
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
