// Sarvam TTS returns a list of base64 WAV chunks (long text gets split);
// play them back to back so a shortlist readback sounds like one utterance.
export function playBase64WavChunks(chunks) {
  return chunks.reduce((chain, base64) => chain.then(() => playOne(base64)), Promise.resolve())
}

function playOne(base64) {
  return new Promise((resolve, reject) => {
    const audio = new Audio(`data:audio/wav;base64,${base64}`)
    audio.onended = resolve
    audio.onerror = () => reject(new Error('Audio playback failed'))
    audio.play().catch(reject)
  })
}

// Plays a sequence of {audio_base64} segments back to back, calling
// onSegmentStart right before each one starts — drives the "now narrating"
// colour highlight in ReadbackStep.
export async function playReadbackSequence(segments, onSegmentStart) {
  for (const segment of segments) {
    onSegmentStart?.(segment)
    await playBase64WavChunks(segment.audio_base64)
  }
}
