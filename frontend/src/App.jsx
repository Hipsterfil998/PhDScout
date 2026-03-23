import { useState } from 'react'
import SearchTab from './components/SearchTab.jsx'
import ResultsTab from './components/ResultsTab.jsx'
import ReviewTab from './components/ReviewTab.jsx'
import ExportTab from './components/ExportTab.jsx'

export default function App() {
  const [tab, setTab] = useState(0)
  const [profile, setProfile] = useState(null)
  const [profileText, setProfileText] = useState('')
  const [scoredJobs, setScoredJobs] = useState([])
  const [approved, setApproved] = useState([])
  const [currentJobIdx, setCurrentJobIdx] = useState(-1)
  const [currentHints, setCurrentHints] = useState(null)
  const [coverLetter, setCoverLetter] = useState('')

  function handleSearchDone({ profile, profileText, scoredJobs }) {
    setProfile(profile)
    setProfileText(profileText)
    setScoredJobs(scoredJobs)
    setCurrentJobIdx(-1)
    setCurrentHints(null)
    setCoverLetter('')
    setTab(1)
  }

  function handleSelectJob(idx) {
    setCurrentJobIdx(idx)
    setCurrentHints(null)
    setCoverLetter('')
    setTab(2)
  }

  function handleApprove(entry) {
    setApproved(prev => {
      const { title, institution } = entry.job
      return prev.some(a => a.job.title === title && a.job.institution === institution)
        ? prev
        : [...prev, entry]
    })
  }

  const TABS = [
    { name: 'Search',  badge: null,                    disabled: false },
    { name: 'Results', badge: scoredJobs.length || null, disabled: scoredJobs.length === 0 },
    { name: 'Review',  badge: null,                    disabled: scoredJobs.length === 0 },
    { name: 'Export',  badge: approved.length || null,  disabled: approved.length === 0 },
  ]

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <header className="bg-gray-900 border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
          <span className="text-2xl">🎓</span>
          <div>
            <h1 className="text-xl font-bold text-white leading-tight">PhdScout</h1>
            <p className="text-xs text-gray-500">AI-powered academic job search</p>
          </div>
          <div className="ml-auto text-xs text-gray-500 hidden sm:block">
            Free · No sign-up · Powered by Groq
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-4">
          <nav className="flex gap-1">
            {TABS.map(({ name, badge, disabled }, i) => (
              <button
                key={name}
                onClick={() => !disabled && setTab(i)}
                className={[
                  'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors',
                  tab === i
                    ? 'border-indigo-500 text-indigo-400'
                    : disabled
                      ? 'border-transparent text-gray-700 cursor-not-allowed'
                      : 'border-transparent text-gray-500 hover:text-gray-300',
                ].join(' ')}
              >
                {name}
                {badge !== null && (
                  <span className="ml-1.5 text-xs bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded-full px-1.5 py-0.5">
                    {badge}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-6">
        {tab === 0 && <SearchTab onDone={handleSearchDone} />}
        {tab === 1 && (
          <ResultsTab
            profile={profile}
            scoredJobs={scoredJobs}
            onSelectJob={handleSelectJob}
            onGoReview={() => setTab(2)}
          />
        )}
        {tab === 2 && (
          <ReviewTab
            scoredJobs={scoredJobs}
            profileText={profileText}
            currentJobIdx={currentJobIdx}
            setCurrentJobIdx={setCurrentJobIdx}
            currentHints={currentHints}
            setCurrentHints={setCurrentHints}
            coverLetter={coverLetter}
            setCoverLetter={setCoverLetter}
            onApprove={handleApprove}
          />
        )}
        {tab === 3 && <ExportTab approved={approved} />}
      </main>

      <footer className="border-t border-gray-800 bg-gray-900">
        <div className="max-w-6xl mx-auto px-4 py-3 text-xs text-gray-500 flex flex-wrap gap-4">
          <span>© 2025 PhdScout</span>
          <span>CVs are processed in memory and never stored</span>
          <span>Sources: Euraxess · ScholarshipDb · Nature Careers · mlscientist.com</span>
        </div>
      </footer>
    </div>
  )
}
