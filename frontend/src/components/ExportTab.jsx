import { useState } from 'react'
import { exportZip } from '../api.js'

export default function ExportTab({ approved }) {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  async function handleExport() {
    if (approved.length === 0) return
    setLoading(true)
    setStatus('')
    setError('')
    try {
      const blob = await exportZip(approved)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'phdscout_applications.zip'
      a.click()
      URL.revokeObjectURL(url)
      setStatus(`✅ Downloaded ZIP with ${approved.length} application(s).`)
    } catch (err) {
      setError('Export failed: ' + (err?.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  if (approved.length === 0) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-500">
          <p className="text-2xl mb-2">📭</p>
          <p>No applications approved yet.</p>
          <p className="text-sm mt-1">Go to the Review tab to approve positions.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Approved applications ({approved.length})</h2>
        <button
          onClick={handleExport}
          disabled={loading}
          className="px-5 py-2.5 text-white text-sm font-semibold rounded-xl transition-all
            bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500
            shadow-lg shadow-indigo-500/20
            disabled:from-gray-700 disabled:to-gray-700 disabled:shadow-none disabled:cursor-not-allowed"
        >
          {loading ? 'Generating ZIP…' : '⬇ Download all as ZIP'}
        </button>
      </div>

      {status && (
        <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-3 text-sm text-emerald-400">
          {status}
        </div>
      )}
      {error && (
        <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="space-y-3">
        {approved.map((entry, i) => {
          const job = entry.job || {}
          const match = job.match || {}
          const institution = job.institution || job.company || 'Unknown'
          const ts = entry.approved_at ? new Date(entry.approved_at).toLocaleString() : ''
          const score = match.match_score
          const scoreCls = score >= 75
            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
            : score >= 55
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              : 'bg-red-500/15 text-red-400 border border-red-500/30'

          return (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-indigo-500/40 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-gray-500">#{i + 1}</span>
                    {score !== undefined && (
                      <span className={`text-xs rounded-full px-2 py-0.5 font-bold ${scoreCls}`}>
                        {score}
                      </span>
                    )}
                    {job.type && <span className="text-xs text-gray-500 capitalize">{job.type}</span>}
                  </div>
                  <h4 className="mt-1 font-semibold text-white text-sm">{job.title || 'Unknown'}</h4>
                  <p className="text-xs text-gray-400">
                    {institution}{job.location ? ` · ${job.location}` : ''}
                  </p>
                  {ts && <p className="text-xs text-gray-500 mt-1">Approved {ts}</p>}
                  {entry.notes && <p className="text-xs text-gray-400 mt-1 italic">Note: {entry.notes}</p>}
                </div>
                {job.url && (
                  <a href={job.url} target="_blank" rel="noreferrer"
                    className="shrink-0 text-xs text-indigo-400 hover:underline">
                    View →
                  </a>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="text-xs text-gray-500 text-center pb-4">
        The ZIP contains a cover letter, notes, and position details JSON for each application.
      </div>
    </div>
  )
}
