const recordButton = document.querySelector("#record");
const stopButton = document.querySelector("#stop");
const againButton = document.querySelector("#again");
const copyButton = document.querySelector("#copy");
const applicantInput = document.querySelector("#applicant-id");
const statusText = document.querySelector("#status");
const timerText = document.querySelector("#timer");
const resultSection = document.querySelector("#result");
const transcriptText = document.querySelector("#transcript");
const languageText = document.querySelector("#language");
const jsonText = document.querySelector("#json");
const profileSection = document.querySelector("#profile");
const profileLoading = document.querySelector("#profile-loading");
const profileFields = document.querySelector("#profile-fields");

let recorder;
let stream;
let chunks = [];
let timer;
let startedAt;
let latestPayload;

const labels = {
  skills: "Skills", years_experience: "Experience", location: "Location", age: "Age",
  physical_capability_notes: "Work capabilities", availability: "Availability",
  min_pay_expectation: "Expected pay", notes: "Other details",
};

function displayValue(key, value, profile) {
  if (key === "location") return [value.area, value.city].filter(Boolean).join(", ") || value.raw_text || "Not provided";
  if (key === "years_experience") return value === null ? "Not provided" : `${value} year${value === 1 ? "" : "s"}`;
  if (key === "min_pay_expectation") return value === null ? "Not provided" : `₹${value.toLocaleString("en-IN")} ${profile.pay_unit || ""}`.trim();
  if (Array.isArray(value)) return value.length ? value.join(", ") : "Not provided";
  return value ?? "Not provided";
}

function renderProfile(profile) {
  profileFields.replaceChildren();
  for (const key of Object.keys(labels)) {
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = labels[key];
    description.textContent = displayValue(key, profile[key], profile);
    profileFields.append(term, description);
  }
  profileSection.hidden = false;
  jsonText.textContent = JSON.stringify(profile, null, 2);
}

async function extractProfile(transcript) {
  profileLoading.hidden = false;
  profileSection.hidden = true;
  copyButton.disabled = true;
  const response = await fetch("/api/extract-profile", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(transcript),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Profile extraction failed.");
  latestPayload = data;
  renderProfile(data);
  copyButton.disabled = false;
}

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.classList.toggle("error", isError);
}

function cleanupStream() {
  stream?.getTracks().forEach((track) => track.stop());
  stream = undefined;
  clearInterval(timer);
}

function updateTimer() {
  const seconds = Math.min(28, Math.floor((Date.now() - startedAt) / 1000));
  timerText.textContent = `00:${String(seconds).padStart(2, "0")}`;
  if (seconds >= 28 && recorder?.state === "recording") recorder.stop();
}

async function startRecording() {
  if (!applicantInput.value.trim()) {
    setStatus("Please enter your applicant ID before recording.", true);
    applicantInput.focus();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    setStatus("Audio recording is not supported in this browser.", true);
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const preferredType = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"]
      .find((type) => MediaRecorder.isTypeSupported(type));
    recorder = new MediaRecorder(stream, preferredType ? { mimeType: preferredType } : undefined);
    chunks = [];
    recorder.ondataavailable = (event) => event.data.size && chunks.push(event.data);
    recorder.onstop = submitRecording;
    recorder.start(250);

    startedAt = Date.now();
    updateTimer();
    timer = setInterval(updateTimer, 250);
    resultSection.hidden = true;
    recordButton.disabled = true;
    stopButton.disabled = false;
    applicantInput.disabled = true;
    setStatus("Listening… speak naturally.");
  } catch (error) {
    cleanupStream();
    setStatus(error.name === "NotAllowedError" ? "Microphone permission was denied." : "Could not start the microphone.", true);
  }
}

async function submitRecording() {
  cleanupStream();
  stopButton.disabled = true;
  setStatus("Transcribing and translating to English…");

  const recordedMimeType = recorder.mimeType || chunks[0]?.type || "audio/webm";
  // Sarvam accepts audio/webm but rejects MIME parameters such as ;codecs=opus.
  const mimeType = recordedMimeType.split(";", 1)[0];
  const audio = new Blob(chunks, { type: mimeType });
  try {
    const response = await fetch("/api/transcribe", {
      method: "POST",
      headers: {
        "content-type": mimeType,
        "x-applicant-id": applicantInput.value.trim(),
      },
      body: audio,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Transcription failed.");

    transcriptText.textContent = data.transcript_en;
    languageText.textContent = data.language;
    resultSection.hidden = false;
    setStatus("Voice captured. Building your work profile…");
    await extractProfile(data);
    setStatus("Your work profile is ready.");
  } catch (error) {
    setStatus(error.message, true);
    recordButton.disabled = false;
    applicantInput.disabled = false;
  } finally { profileLoading.hidden = true; }
}

recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", () => recorder?.state === "recording" && recorder.stop());
againButton.addEventListener("click", () => {
  resultSection.hidden = true;
  profileSection.hidden = true;
  copyButton.disabled = true;
  recordButton.disabled = false;
  applicantInput.disabled = false;
  timerText.textContent = "00:00";
  setStatus("Ready to record (maximum 28 seconds)");
});
copyButton.addEventListener("click", async () => {
  await navigator.clipboard.writeText(JSON.stringify(latestPayload, null, 2));
  copyButton.textContent = "Copied";
  setTimeout(() => (copyButton.textContent = "Copy profile JSON"), 1200);
});
