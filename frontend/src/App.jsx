import { useState, useRef } from "react";

import axios from "axios";

import {
  Brain,
  Upload,
  Mic,
  Square,
  LoaderCircle,
  FileText,
  CheckCircle,
  Target,
  AlertTriangle,
  List,
} from "lucide-react";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const formatTranscriptTime = (seconds) => {
  const totalSeconds = Math.floor(Number(seconds));
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const remainingSeconds = String(totalSeconds % 60).padStart(2, "0");

  return `${minutes}:${remainingSeconds}`;
};

const parseTranscript = (transcript) =>
  transcript
    .split(/\r?\n/)
    .filter((line) => line.trim())
    .map((line) => {
      const match = line.match(/^\[(\d+(?:\.\d+)?)s\s*-\s*(\d+(?:\.\d+)?)s\]\s*(.*)$/);

      if (!match) {
        return { text: line.trim() };
      }

      return {
        start: formatTranscriptTime(match[1]),
        end: formatTranscriptTime(match[2]),
        text: match[3],
      };
    });

function App() {

  const [analysis, setAnalysis] = useState(null);
  const [transcript, setTranscript] = useState("");
  const [processing, setProcessing] = useState(false);
  const [recording, setRecording] = useState(false);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const processAudio = async (audioFile) => {
    setProcessing(true);
    setError("");
    setAnalysis(null);
    setTranscript("");
    setFileName(audioFile.name);

    try {
      const formData = new FormData();
      formData.append("file", audioFile);

      const response = await axios.post(
        `${API_URL}/process-meeting`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          timeout: 30 * 60 * 1000,
        }
      );

      if (!response.data.success) {
        throw new Error(
          response.data.details ||
          response.data.error ||
          "Meeting processing failed."
        );
      }

      setAnalysis(response.data.analysis);

      try {
        const transcriptResponse = await axios.get(
          `${API_URL}/transcript`
        );

        setTranscript(
          typeof transcriptResponse.data.transcript === "string"
            ? transcriptResponse.data.transcript
            : ""
        );
      } catch (transcriptError) {
        console.error(transcriptError);
      }
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.details ||
        err.response?.data?.error ||
        err.message ||
        "Unable to process the meeting."
      );
    } finally {
      setProcessing(false);
    }
  };

  // ========================================================
  // UPLOAD
  // ========================================================

  const handleUpload = (event) => {

    const file =
      event.target.files[0];

    if (!file) {
      return;
    }

    processAudio(file);
  };

  // ========================================================
  // START RECORDING
  // ========================================================

  const startRecording = async () => {

    try {

      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      const recorder =
        new MediaRecorder(stream);

      mediaRecorderRef.current =
        recorder;

      audioChunksRef.current = [];

      recorder.ondataavailable =
        (event) => {

          if (event.data.size > 0) {

            audioChunksRef.current.push(
              event.data
            );

          }

        };

      recorder.onstop = async () => {

        const audioBlob =
          new Blob(
            audioChunksRef.current,
            {
              type: "audio/webm",
            }
          );

        const recordedFile =
          new File(
            [audioBlob],
            "recorded_meeting.webm",
            {
              type: "audio/webm",
            }
          );

        stream
          .getTracks()
          .forEach(
            (track) =>
              track.stop()
          );

        await processAudio(
          recordedFile
        );

      };

      recorder.start();

      setRecording(true);

    } catch (err) {

      console.error(err);

      setError(
        "Microphone permission was denied or unavailable."
      );

    }
  };

  // ========================================================
  // STOP RECORDING
  // ========================================================

  const stopRecording = () => {

    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !==
        "inactive"
    ) {

      mediaRecorderRef.current.stop();

    }

    setRecording(false);

  };

  // ========================================================
  // UI
  // ========================================================

  return (

    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div className="brand">

          <div className="logo">

            <Brain size={30} />

          </div>

          <div>

            <h1>MeetIQ</h1>

            <p>
              AI Meeting Intelligence
            </p>

          </div>

        </div>

        <div className="status">

          <span className="status-dot"></span>

          Backend Connected

        </div>

      </header>

      {/* MAIN */}

      <main className="container">

        {/* HERO */}

        <section className="hero">

          <p className="eyebrow">
            AI MEETING INTELLIGENCE
          </p>

          <h2>
            Turn conversations into insights.
          </h2>

          <p className="hero-text">

            Record or upload a meeting and
            let MeetIQ automatically generate
            actionable intelligence.

          </p>

        </section>

        {/* UPLOAD / RECORD */}

        {!processing && !analysis && (

          <section className="upload-card">

            <div className="upload-icon">

              <Upload size={32} />

            </div>

            <h3>
              Add your meeting
            </h3>

            <p>
              Upload a meeting recording or
              record one directly.
            </p>

            <div className="meeting-buttons">

              {/* UPLOAD */}

              <label
                className="primary-button"
              >

                <Upload size={19} />

                Upload Recording

                <input
                  type="file"
                  accept="audio/*,video/*"
                  onChange={handleUpload}
                  hidden
                />

              </label>

              {/* RECORD */}

              {!recording ? (

                <button
                  className="secondary-button"
                  onClick={
                    startRecording
                  }
                >

                  <Mic size={19} />

                  Record Meeting

                </button>

              ) : (

                <button
                  className="recording-button"
                  onClick={
                    stopRecording
                  }
                >

                  <Square size={18} />

                  Stop Recording

                </button>

              )}

            </div>

            {recording && (

              <div className="recording-status">

                <span className="recording-dot"></span>

                Recording in progress...

              </div>

            )}

          </section>

        )}

        {/* PROCESSING */}

        {processing && (

          <section className="processing-card">

            <LoaderCircle
              size={45}
              className="spinner"
            />

            <h3>
              MeetIQ is analyzing your meeting
            </h3>

            <p>
              Transcribing the recording and
              extracting meeting intelligence...
            </p>

            <div className="processing-steps">

              <span>
                🎙 Transcribing audio
              </span>

              <span>
                🧠 Analyzing conversation
              </span>

              <span>
                📊 Extracting insights
              </span>

            </div>

          </section>

        )}

        {/* ERROR */}

        {error && (

          <div className="error-box">

            <AlertTriangle size={20} />

            {error}

          </div>

        )}

        {/* RESULTS */}

        {analysis && !processing && (

          <section className="results">

            <div className="meeting-file">

              <FileText size={18} />

              {fileName}

            </div>

            {/* SUMMARY */}

            <section className="summary-card">

              <div className="section-title">

                <div className="icon-box">

                  <FileText size={22} />

                </div>

                <div>

                  <h3>
                    Meeting Summary
                  </h3>

                  <p>
                    AI-generated overview
                  </p>

                </div>

              </div>

              <p className="summary-text">

                {analysis.summary}

              </p>

            </section>

            {/* GRID */}

            <section className="dashboard-grid">

              {/* TOPICS */}

              <div className="card">

                <div className="card-title">

                  <div className="icon-box blue">

                    <List size={21} />

                  </div>

                  <h3>
                    Key Topics
                  </h3>

                </div>

                <div className="tag-container">

                  {analysis.key_topics?.map(
                    (topic, index) => (

                      <span
                        className="topic-tag"
                        key={index}
                      >
                        {topic}
                      </span>

                    )
                  )}

                </div>

              </div>

              {/* DECISIONS */}

              <div className="card">

                <div className="card-title">

                  <div className="icon-box green">

                    <CheckCircle size={21} />

                  </div>

                  <h3>
                    Decisions
                  </h3>

                </div>

                <ul className="list">

                  {analysis.decisions?.map(
                    (decision, index) => (

                      <li key={index}>
                        {decision}
                      </li>

                    )
                  )}

                </ul>

              </div>

            </section>

            {/* ACTION ITEMS */}

            <section className="full-width-card">

              <div className="section-title">

                <div className="icon-box orange">
                  <Target size={21} />
                </div>

                <div>
                  <h3>Action Items</h3>
                  <p>Tasks identified from the meeting</p>
                </div>

              </div>

              {analysis.action_items?.length > 0 ? (

                <div className="full-width-action-list">

                  {analysis.action_items.map(
                    (item, index) => (

                      <div
                        className="full-width-action-item"
                        key={index}
                      >

                        <Square
                          className="action-checkbox-icon"
                          size={19}
                          aria-hidden="true"
                        />

                        <div className="action-item-content">

                          <strong>{item.task}</strong>

                          <div className="action-meta">
                            <span>
                              Owner: {item.owner?.trim() || "Not specified"}
                            </span>

                            <span>
                              Deadline: {item.deadline?.trim() || "Not specified"}
                            </span>
                          </div>

                        </div>

                      </div>

                    )
                  )}

                </div>

              ) : (

                <p className="empty">
                  No action items identified.
                </p>

              )}

            </section>

            {/* UNRESOLVED ISSUES */}

            <section className="full-width-card">

              <div className="section-title">

                <div className="icon-box red">
                  <AlertTriangle size={21} />
                </div>

                <div>
                  <h3>Unresolved Issues</h3>
                  <p>Topics that still need attention</p>
                </div>

              </div>

              {analysis.unresolved_issues?.length > 0 ? (

                <ul className="list warning-list full-width-issue-list">

                  {analysis.unresolved_issues.map(
                    (issue, index) => (

                      <li key={index}>
                        {issue}
                      </li>

                    )
                  )}

                </ul>

              ) : (

                <p className="empty">
                  No unresolved issues identified.
                </p>

              )}

            </section>

            {/* TRANSCRIPT */}

            <section className="full-width-card transcript-card">

              <div className="section-title">

                <div className="icon-box">
                  <FileText size={22} />
                </div>

                <div>
                  <h3>Meeting Transcript</h3>
                  <p>Full conversation with timestamps</p>
                </div>

              </div>

              <div className="transcript-scroll">

                {transcript ? (

                  parseTranscript(transcript).map(
                    (segment, index) => (

                      segment.start ? (

                        <article
                          className="transcript-segment"
                          key={index}
                        >
                          <div className="transcript-time">
                            {segment.start} - {segment.end}
                          </div>

                          <p>{segment.text}</p>
                        </article>

                      ) : (

                        <p
                          className="transcript-plain-text"
                          key={index}
                        >
                          {segment.text}
                        </p>

                      )

                    )
                  )

                ) : (

                  <p className="empty">
                    Transcript not available.
                  </p>

                )}

              </div>

            </section>

          </section>

        )}

      </main>

    </div>

  );
}

export default App;
