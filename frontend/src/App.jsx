import { useState } from 'react'
import FinalOutputStep from './components/FinalOutputStep.jsx'
import IntakeStep from './components/IntakeStep.jsx'
import ProfileStep from './components/ProfileStep.jsx'
import ReadbackStep from './components/ReadbackStep.jsx'
import StepIndicator from './components/StepIndicator.jsx'
import SearchStep from './components/SearchStep.jsx'
import { APPLICANT_ID, emptyProfile } from './data/profile.js'

const STEP = {
  INTAKE: 0,
  PROFILE: 1,
  SEARCH: 2,
  READBACK: 3,
  FINAL: 4,
}

function App() {
  const [step, setStep] = useState(STEP.INTAKE)
  const [transcript, setTranscript] = useState('')
  const [profile, setProfile] = useState(emptyProfile())
  const [shortlistPostings, setShortlistPostings] = useState([])
  const [sessionId, setSessionId] = useState(null)

  const restart = () => {
    setTranscript('')
    setProfile(emptyProfile())
    setShortlistPostings([])
    setSessionId(null)
    setStep(STEP.INTAKE)
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Kaam Sahayak</h1>
        <p className="muted">Voice-first job matching, demo shell</p>
      </header>

      <StepIndicator current={step} />

      <main className="app-main">
        {step === STEP.INTAKE && (
          <IntakeStep
            transcript={transcript}
            onChange={setTranscript}
            onNext={(extractedProfile) => {
              setProfile(extractedProfile)
              setStep(STEP.PROFILE)
            }}
          />
        )}

        {step === STEP.PROFILE && (
          <ProfileStep
            profile={profile}
            onChange={setProfile}
            onBack={() => setStep(STEP.INTAKE)}
            onNext={() => setStep(STEP.SEARCH)}
          />
        )}

        {step === STEP.SEARCH && (
          <SearchStep
            profile={profile}
            onFound={setShortlistPostings}
            onBack={() => setStep(STEP.PROFILE)}
            onNext={() => setStep(STEP.READBACK)}
          />
        )}

        {step === STEP.READBACK && (
          <ReadbackStep
            profile={profile}
            postings={shortlistPostings}
            onBack={() => setStep(STEP.SEARCH)}
            onDone={(sid) => {
              setSessionId(sid)
              setStep(STEP.FINAL)
            }}
          />
        )}

        {step === STEP.FINAL && (
          <FinalOutputStep
            applicantId={APPLICANT_ID}
            sessionId={sessionId}
            onStartOver={restart}
          />
        )}
      </main>
    </div>
  )
}

export default App
