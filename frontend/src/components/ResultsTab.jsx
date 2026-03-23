import { useState } from 'react'
import { REC_CONFIG } from '../constants.js'

function ProfileCard({ profile }) {
  if (!profile) return null
  const contact = profile.contact || {}
  const interests = profile.research_interests || []
  const education = profile.education || []
  const skills = profile.skills || {}
  const allSkills = [...(skills.programming || []), ...(skills.tools || [])].slice(0, 12)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
      <div>
        <h3 className="font-bold text-white text-lg">{profile.name || 'Unknown'}</h3>
        {contact.email && <p className="text-xs text-gray-500">{contact.email}</p>}
        {contact.linkedin && (
          <a href={contact.linkedin} target="_blank" rel="noreferrer"
            className="text-xs text-indigo-400 hover:underline">LinkedIn</a>
        )}
      </div>
      {profile.summary && (
        <p className="text-sm text-gray-400 leading-relaxed">{profile.summary}</p>
      )}
      {interests.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-1">Research interests</p>
          <div className="flex flex-wrap gap-1">
            {interests.map((item, idx) => (
              <span key={idx} className="text-xs bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 rounded-full px-2 py-0.5">
                {item}
              </span>
            ))}
          </div>
        </div>
      )}
      {education.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-1">Education</p>
          {education.slice(0, 2).map((e, idx) => (
            <p key={idx} className="text-xs text-gray-400">
              {e.degree} in {e.field} — {e.institution} ({e.year})
            </p>
          ))}
        </div>
      )}
      {allSkills.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-1">Skills</p>
          <p className="text-xs text-gray-400">{allSkills.join(', ')}</p>
        </div>
      )}
    </div>
  )
}

function ScoreBadge({ score }) {
  const cls = score >= 75
    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
    : score >= 55
      ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
      : 'bg-red-500/15 text-red-400 border border-red-500/30'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${cls}`}>
      {score}
    </span>
  )
}

function JobCard({ job, idx, onSelect }) {
  const match = job.match || {}
  const score = match.match_score || 0
  const rec = match.recommendation || ''
  const recCfg = REC_CONFIG[rec] || {}
  const institution = job.institution || job.company || ''

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-indigo-500/40 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <ScoreBadge score={score} />
            {rec && (
              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${recCfg.color || ''}`}>
                {recCfg.icon} {recCfg.label}
              </span>
            )}
            {job.freshness && <span className="text-xs text-gray-500">{job.freshness}</span>}
          </div>
          <h4 className="mt-1.5 font-semibold text-white text-sm leading-snug">
            <a href={job.url} target="_blank" rel="noreferrer" className="hover:text-indigo-400 hover:underline">
              {job.title}
            </a>
          </h4>
          <p className="text-xs text-gray-500 mt-0.5">
            {institution}
            {institution && job.location ? ' · ' : ''}
            {job.location}
            {job.type ? ` · ${job.type}` : ''}
          </p>
          {match.why_good_fit && (
            <p className="mt-1.5 text-xs text-gray-400 line-clamp-2">
              <span className="font-medium text-gray-300">Why: </span>
              {match.why_good_fit}
            </p>
          )}
          {job.deadline && <p className="mt-1 text-xs text-gray-500">Deadline: {job.deadline}</p>}
        </div>
        <button
          onClick={() => onSelect(idx)}
          className="shrink-0 text-xs text-white font-medium px-3 py-1.5 rounded-lg transition-all
            bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500
            shadow-lg shadow-indigo-500/20"
        >
          Review →
        </button>
      </div>
    </div>
  )
}

export default function ResultsTab({ profile, scoredJobs, onSelectJob }) {
  const [minScore, setMinScore] = useState(0)

  const filtered = scoredJobs.filter(j => (j.match?.match_score || 0) >= minScore)
  const applying = filtered.filter(j => j.match?.recommendation === 'apply').length
  const considering = filtered.filter(j => j.match?.recommendation === 'consider').length

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex-1">
          <h2 className="text-xl font-bold text-white">{scoredJobs.length} positions found</h2>
          <p className="text-sm text-gray-400">✅ {applying} to apply · 🟡 {considering} to consider</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400 whitespace-nowrap">
            Min score: <span className="font-bold text-indigo-400">{minScore}</span>
          </label>
          <input
            type="range" min={0} max={90} step={5}
            value={minScore}
            onChange={e => setMinScore(Number(e.target.value))}
            className="w-28 accent-indigo-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2">Your profile</p>
          <ProfileCard profile={profile} />
        </div>
        <div className="lg:col-span-2 space-y-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            Positions ({filtered.length})
          </p>
          {filtered.length === 0 ? (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
              No positions above score {minScore}. Lower the filter to see more.
            </div>
          ) : (
            filtered.map((job, idx) => (
              <JobCard
                key={job.url || idx}
                job={job}
                idx={scoredJobs.indexOf(job)}
                onSelect={onSelectJob}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
