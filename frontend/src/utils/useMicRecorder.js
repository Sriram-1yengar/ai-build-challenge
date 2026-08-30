import { useCallback, useRef, useState } from 'react'

// Records a single question from the mic and resolves the finished clip as a Blob.
// Used against the real Phase 5 /ask-audio endpoint (Sarvam STT+Translate server-side).
export function useMicRecorder() {
  const [recording, setRecording] = useState(false)
  const [error, setError] = useState(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])

  const start = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : ''
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.start()
      recorderRef.current = recorder
      setRecording(true)
    } catch (err) {
      setError(err.message || 'Microphone access was denied')
    }
  }, [])

  const stop = useCallback(() => {
    return new Promise((resolve) => {
      const recorder = recorderRef.current
      if (!recorder) {
        resolve(null)
        return
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        recorder.stream.getTracks().forEach((track) => track.stop())
        setRecording(false)
        resolve(blob)
      }
      recorder.stop()
    })
  }, [])

  return { recording, error, start, stop }
}
