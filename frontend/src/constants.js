export const LOCATIONS = [
  'Worldwide',
  'Europe (all)',
  // Western Europe
  'UK', 'Germany', 'France', 'Italy', 'Spain', 'Netherlands',
  'Switzerland', 'Belgium', 'Austria', 'Portugal', 'Ireland',
  // Nordic
  'Sweden', 'Denmark', 'Finland', 'Norway',
  // Central / Eastern Europe
  'Poland', 'Czech Republic', 'Hungary', 'Romania', 'Greece',
  'Croatia', 'Slovakia', 'Slovenia', 'Bulgaria', 'Estonia',
  'Latvia', 'Lithuania', 'Luxembourg', 'Serbia', 'Turkey',
  // Americas
  'United States', 'Canada', 'Brazil',
  // Asia-Pacific
  'Australia', 'Japan', 'South Korea', 'China', 'Singapore',
  'India', 'New Zealand',
  // Other
  'South Africa', 'Israel',
]

export const POSITION_TYPES = [
  { value: 'phd',            label: 'PhD position' },
  { value: 'predoctoral',    label: 'Predoctoral' },
  { value: 'postdoc',        label: 'Postdoc' },
  { value: 'fellowship',     label: 'Fellowship' },
  { value: 'research_staff', label: 'Research staff' },
]

export const REC_CONFIG = {
  apply:    { icon: '✅', label: 'Apply',    color: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30' },
  consider: { icon: '🟡', label: 'Consider', color: 'text-amber-400 bg-amber-500/15 border-amber-500/30' },
  skip:     { icon: '❌', label: 'Skip',     color: 'text-red-400 bg-red-500/15 border-red-500/30' },
}
