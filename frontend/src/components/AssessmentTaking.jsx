import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle, Camera, Eye, Clock, Send, X } from 'lucide-react';
import api from '../services/api';

const AssessmentTaking = ({ user, onComplete, onExit }) => {
  const [assessment, setAssessment] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [warnings, setWarnings] = useState([]);
  const [faceVerified, setFaceVerified] = useState(false);
  const [showFaceVerification, setShowFaceVerification] = useState(true);
  const [cheatingStatus, setCheatingStatus] = useState({
    face_verified: false,
    face_confidence: 0,
    multiple_faces: false,
    face_count: 0,
    phone_detected: false,
    phone_count: 0,
    overall_status: 'safe'
  });

  const videoRef = useRef(null);
  const monitorIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    loadAssessment();
    return () => cleanup();
  }, []);

  // Start camera only when face verification screen is shown
  useEffect(() => {
    if (showFaceVerification && !loading && !error && !streamRef.current) {
      console.log('[CAMERA] Face verification screen shown, starting camera...');
      startCamera();
    }
  }, [showFaceVerification, loading, error]);

  // Re-bind stream to video when overlay hides and exam UI video renders
  useEffect(() => {
    if (!showFaceVerification && streamRef.current && videoRef.current) {
      console.log('[CAMERA] Binding stream to exam video element');
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.muted = true;
      const play = async () => {
        try {
          await videoRef.current.play();
          console.log('[CAMERA] Exam video playing');
        } catch (e) {
          console.log('[CAMERA] Exam video play() error:', e?.message || e);
        }
      };
      play();
    }
  }, [showFaceVerification]);

  // Start monitoring as soon as face is verified
  useEffect(() => {
    if (faceVerified && assessment) {
      console.log('[MONITOR] ✅ Conditions met - starting monitoring NOW');
      setTimeout(() => {
        startMonitoring();
        startTimer();
      }, 500);
    }
  }, [faceVerified, assessment]);

  const loadAssessment = async () => {
    try {
      const code = localStorage.getItem('currentAssessmentCode');
      if (!code) throw new Error('No assessment code found');

      const data = await api.accessAssessment(code);
      setAssessment(data);
      setTimeRemaining(data.duration_minutes * 60);

      const initialAnswers = {};
      data.questions.forEach(q => { initialAnswers[q.id] = ''; });
      setAnswers(initialAnswers);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const startCamera = async () => {
    try {
      // Prevent multiple camera starts unless stream is inactive/ended
      if (streamRef.current) {
        const tracks = streamRef.current.getTracks ? streamRef.current.getTracks() : [];
        const allEnded = tracks.length > 0 && tracks.every(t => t.readyState === 'ended');
        const active = typeof streamRef.current.active === 'boolean' ? streamRef.current.active : !allEnded;
        if (active && !allEnded) {
          console.log('[CAMERA] Camera already running');
          return;
        }
        console.log('[CAMERA] Previous stream inactive/ended. Re-acquiring...');
        try { tracks.forEach(t => t.stop()); } catch {}
        streamRef.current = null;
      }

      if (!videoRef.current) {
        console.log('[CAMERA] Video element not ready yet');
        return;
      }

      console.log('[CAMERA] 📹 Starting camera...');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false
      });
      
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      videoRef.current.muted = true;
      
      // Wait for metadata before playing
      await new Promise((resolve) => {
        videoRef.current.onloadedmetadata = resolve;
      });
      
      // Start playing the video stream
      try { await videoRef.current.play(); } catch (e) { console.warn('[CAMERA] play() blocked:', e); }
      
      // Ensure readyState is sufficient
      const waitForReady = async (timeoutMs = 2000) => {
        const start = Date.now();
        while (Date.now() - start < timeoutMs) {
          if (videoRef.current && videoRef.current.readyState >= 2) return true;
          await new Promise(r => setTimeout(r, 50));
        }
        return false;
      };
      const ok = await waitForReady();
      if (!ok) {
        alert('Camera not ready. Please allow camera access and try again.');
        return;
      }
      
      console.log('[CAMERA] ✅ Camera started successfully');
    } catch (err) {
      console.error('[CAMERA] ❌ Error:', err);
      setError('Camera access required for exam monitoring');
    }
  };

  const verifyFace = async () => {
    try {
      if (!videoRef.current) {
        alert('Video not ready');
        return;
      }

      if (!videoRef.current || !(videoRef.current instanceof HTMLVideoElement)) {
        alert('Camera element not available. Please reload the page.');
        return;
      }
      if (!videoRef.current.srcObject) {
        alert('Camera stream not available. Please allow camera access.');
        return;
      }
      if (videoRef.current.readyState < 2) {
        try { await videoRef.current.play(); } catch {}
      }
      if (!videoRef.current.videoWidth || !videoRef.current.videoHeight) {
        alert('Please wait for camera to initialize');
        return;
      }

      const canvas = document.createElement('canvas');
      const vw = videoRef.current.videoWidth || 480;
      const vh = videoRef.current.videoHeight || 360;
      const targetW = Math.min(640, vw);
      const targetH = Math.max(1, Math.floor(vh * (targetW / vw)));
      canvas.width = targetW;
      canvas.height = targetH;
      
      if (canvas.width === 0 || canvas.height === 0) {
        alert('Camera not ready. Please wait a moment.');
        return;
      }

      const context = canvas.getContext('2d');
      const ensureFrame = async () => {
        if (!videoRef.current || videoRef.current.readyState < 2) {
          await new Promise(r => setTimeout(r, 50));
        }
        context.drawImage(videoRef.current, 0, 0, targetW, targetH);
      };
      await ensureFrame();
      let best = 0;
      let passed = false;
      for (let i = 0; i < 7; i++) {
        if (!videoRef.current || videoRef.current.readyState < 2) {
          try { await videoRef.current.play(); } catch {}
          await new Promise(r => setTimeout(r, 80));
        }
        const shot = canvas.toDataURL('image/jpeg', 0.95);
        if (!shot || shot === 'data:,') continue;
        const r = await api.verifyFace(shot);
        if (r && typeof r.confidence === 'number') best = Math.max(best, r.confidence);
        if (r.verified && r.confidence > 80) { passed = true; break; }
        await new Promise(res => setTimeout(res, 150));
        await ensureFrame();
      }
      if (passed) {
        // Enter fullscreen immediately upon successful verification
        enterFullscreen();
        setFaceVerified(true);
        setShowFaceVerification(false);
      } else {
        alert(`Face verification failed (${best.toFixed(1)}%). Please try again.`);
      }
    } catch (err) {
      console.error('[VERIFY] ❌ Error:', err);
      alert('Face verification error: ' + err.message);
    }
  };

  const enterFullscreen = () => {
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
      elem.requestFullscreen().catch(e => console.log('[FULLSCREEN] Not supported:', e));
    } else if (elem.webkitRequestFullscreen) {
      elem.webkitRequestFullscreen();
    }
  };

  const startMonitoring = () => {
    console.log('[MONITOR] 🚀 STARTING MONITORING SYSTEM');
    console.log('[MONITOR] Video:', !!videoRef.current);
    console.log('[MONITOR] Stream:', !!streamRef.current);
    
    // Monitor for fullscreen/tab changes
    document.addEventListener('fullscreenchange', () => {
      if (!document.fullscreenElement) {
        addWarning('⚠️ Exited fullscreen mode');
      }
    });
    
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        addWarning('⚠️ Switched to another tab/window');
      }
    });

    // CRITICAL: Start interval monitoring
    monitorIntervalRef.current = setInterval(() => {
      console.log('[MONITOR] 🔄 Running check...');
      monitorCheatingAttempts();
    }, 3000);
    
    // Run first check immediately
    console.log('[MONITOR] 🎯 Running FIRST check NOW...');
    monitorCheatingAttempts();
  };

  const monitorCheatingAttempts = async () => {
    try {
      if (!videoRef.current || !streamRef.current) {
        console.log('[MONITOR] Video/stream not available');
        // Try to recover camera
        await startCamera();
        if (!streamRef.current) return;
      }

      const canvas = document.createElement('canvas');
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;

      if (canvas.width === 0 || canvas.height === 0) {
        console.log('[MONITOR] Video dimensions are 0');
        // Attempt to re-bind and retry once
        if (streamRef.current) {
          videoRef.current.srcObject = streamRef.current;
          try { await videoRef.current.play(); } catch {}
        }
        return;
      }
      
      const context = canvas.getContext('2d');
      context.drawImage(videoRef.current, 0, 0);
      const imageData = canvas.toDataURL('image/jpeg', 0.9);
      
      if (!imageData || imageData === 'data:,') {
        console.log('[MONITOR] ⚠️ Failed to capture image');
        return;
      }
      
      console.log('[MONITOR] 📤 Sending to backend, size:', imageData.length, 'bytes');
      const response = await api.monitorCheating(imageData);
      console.log('[MONITOR] 📥 Response:', response);
      
      setCheatingStatus(response);
      
      // Handle warnings
      if (response.overall_status !== 'safe') {
        let msg = '';
        if (response.overall_status === 'face_mismatch') {
          msg = `❌ Wrong person detected (${response.face_confidence.toFixed(0)}% confidence)`;
        } else if (response.overall_status === 'multiple_faces') {
          msg = `👥 Multiple faces detected (${response.face_count} people)`;
        } else if (response.overall_status === 'phone_detected') {
          msg = `📱 Phone detected in frame`;
        } else {
          msg = '⚠️ Suspicious activity detected';
        }
        addWarning(msg);
      }
      
    } catch (error) {
      console.error('[MONITOR] ❌ Error:', error);
    }
  };

  const startTimer = () => {
    timerIntervalRef.current = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          handleSubmit(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const addWarning = (message) => {
    console.log('[WARNING] ⚠️', message);
    setWarnings(prev => {
      const newWarnings = [...prev, { message, timestamp: new Date().toISOString() }];
      
      if (newWarnings.length >= 10) {
        setTimeout(() => {
          alert('⚠️ EXCESSIVE WARNINGS! Assessment will be auto-submitted.');
          handleSubmit(true);
        }, 1000);
      }
      
      return newWarnings;
    });
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers({ ...answers, [questionId]: value });
  };

  const handleSubmit = async (autoSubmit = false) => {
    if (!autoSubmit && !window.confirm('Submit assessment? You cannot change answers after submission.')) {
      return;
    }

    try {
      const submissionData = {
        assessment_id: assessment.id,
        answers: assessment.questions.map((q, index) => ({
          question_id: q.id,
          question_number: index + 1,
          student_answer: answers[q.id] || ''
        }))
      };

      await api.submitAssessment(submissionData);
      cleanup();
      alert('✅ Assessment submitted successfully!');
      onComplete();
    } catch (err) {
      alert('Error submitting: ' + err.message);
    }
  };

  const cleanup = () => {
    console.log('[CLEANUP] Stopping...');
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (monitorIntervalRef.current) clearInterval(monitorIntervalRef.current);
    if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    document.removeEventListener('fullscreenchange', () => {});
    document.removeEventListener('visibilitychange', () => {});
  };

  // Face Verification Screen
  if (showFaceVerification && !loading && !error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 max-w-2xl w-full mx-4">
          <div className="text-center mb-6">
            <Camera className="w-16 h-16 text-purple-600 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-gray-800 mb-2">Face Verification</h2>
            <p className="text-gray-600">Verify your identity before starting</p>
          </div>

          <div className="relative bg-gray-900 rounded-xl overflow-hidden mb-6">
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-96 object-cover" />
          </div>

          <div className="flex space-x-4">
            <button
              onClick={verifyFace}
              className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700"
            >
              Verify & Start
            </button>
            <button onClick={() => { cleanup(); onExit(); }} className="px-6 bg-gray-300 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-400">
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 max-w-md text-center shadow-xl">
          <AlertTriangle className="w-16 h-16 text-red-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button onClick={onExit} className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const question = assessment.questions[currentQuestion];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">{assessment.title}</h1>
              <p className="text-gray-600">Question {currentQuestion + 1} of {assessment.questions.length}</p>
            </div>
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2 bg-red-50 px-4 py-2 rounded-lg">
                <Clock className={`w-5 h-5 ${timeRemaining < 300 ? 'text-red-600' : 'text-gray-600'}`} />
                <span className={`text-xl font-bold ${timeRemaining < 300 ? 'text-red-600' : 'text-gray-800'}`}>
                  {formatTime(timeRemaining)}
                </span>
              </div>
              <div className="flex items-center space-x-2 bg-green-50 px-4 py-2 rounded-lg">
                <Camera className="w-5 h-5 text-green-600" />
                <span className="text-sm text-green-600 font-semibold">Monitoring</span>
              </div>
              {warnings.length > 0 && (
                <div className="flex items-center space-x-2 bg-yellow-50 px-4 py-2 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <span className="text-sm text-yellow-600 font-semibold">{warnings.length} warning{warnings.length > 1 ? 's' : ''}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
          <div className="mb-6">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold text-gray-800">Question {currentQuestion + 1}</h2>
              <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-semibold">{question.marks} marks</span>
            </div>
            <p className="text-gray-700 text-lg whitespace-pre-wrap">{question.question_text}</p>
          </div>

          {/* Answer Input */}
          {question.question_type === 'mcq' && question.options ? (
            <div className="space-y-3">
              {question.options.map((option, index) => (
                <label key={index} className="flex items-center space-x-3 p-4 border-2 border-gray-200 rounded-lg hover:border-purple-300 cursor-pointer">
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    value={option}
                    checked={answers[question.id] === option}
                    onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                    className="w-4 h-4 text-purple-600"
                  />
                  <span className="text-gray-700">{option}</span>
                </label>
              ))}
            </div>
          ) : (
            <textarea
              value={answers[question.id] || ''}
              onChange={(e) => handleAnswerChange(question.id, e.target.value)}
              placeholder="Type your answer here..."
              className="w-full p-4 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:outline-none min-h-[200px]"
            />
          )}
        </div>

        {/* Navigation */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <span className="text-gray-600 font-semibold">Question Navigation</span>
          </div>
          
          <div className="grid grid-cols-10 gap-2 mb-6">
            {assessment.questions.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentQuestion(index)}
                className={`w-10 h-10 rounded-lg font-semibold ${
                  index === currentQuestion
                    ? 'bg-purple-600 text-white'
                    : answers[assessment.questions[index].id]
                    ? 'bg-green-100 text-green-800 border-2 border-green-300'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {index + 1}
              </button>
            ))}
          </div>

          {currentQuestion < assessment.questions.length - 1 ? (
            <button onClick={() => setCurrentQuestion(currentQuestion + 1)} className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700">
              Next
            </button>
          ) : (
            <button onClick={() => handleSubmit(false)} className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 shadow-lg flex items-center">
              <Send className="w-5 h-5 mr-2" />
              Submit Assessment
            </button>
          )}
        </div>
      </div>

      {/* Live Video Feed */}
      <div className="fixed bottom-24 right-6 z-50">
        <div className="bg-white rounded-xl shadow-2xl overflow-hidden border-4 border-purple-600">
          <div className="bg-purple-600 px-3 py-1 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Camera className="w-4 h-4 text-white" />
              <span className="text-white text-sm font-semibold">Live Feed</span>
            </div>
            <div className={`w-2 h-2 rounded-full ${cheatingStatus.overall_status === 'safe' ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
          </div>
          <video ref={videoRef} autoPlay playsInline muted className="w-64 h-48 object-cover bg-black" />
          <div className="bg-gray-900 px-3 py-2 text-xs text-white">
            <div className="flex justify-between">
              <span>Face: {cheatingStatus.face_verified ? '✓' : '✗'}</span>
              <span>Conf: {cheatingStatus.face_confidence.toFixed(0)}%</span>
            </div>
            <div className="flex justify-between mt-1">
              <span>Count: {cheatingStatus.face_count}</span>
              <span>Phone: {cheatingStatus.phone_detected ? '⚠' : '✓'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Warnings Panel */}
      <div className="fixed bottom-6 left-6 z-50 max-w-sm">
        <div className={`bg-white rounded-xl shadow-2xl overflow-hidden border-2 ${warnings.length > 0 ? 'border-yellow-500' : 'border-green-500'}`}>
          <div className={`px-4 py-2 flex items-center justify-between ${warnings.length > 0 ? 'bg-yellow-500' : 'bg-green-500'}`}>
            <div className="flex items-center space-x-2">
              {warnings.length > 0 ? <AlertTriangle className="w-5 h-5 text-white" /> : <Eye className="w-5 h-5 text-white" />}
              <span className="text-white font-bold">{warnings.length > 0 ? `Warnings (${warnings.length}/10)` : 'Monitoring Active'}</span>
            </div>
            {warnings.length >= 10 && <span className="bg-red-600 text-white px-2 py-1 rounded text-xs font-bold">MAX!</span>}
          </div>
          <div className="max-h-64 overflow-y-auto bg-white">
            {warnings.length > 0 ? (
              warnings.slice(-5).reverse().map((warning, index) => (
                <div key={index} className="px-4 py-3 border-b border-gray-200 last:border-b-0">
                  <p className="text-sm text-gray-800 font-medium">{warning.message}</p>
                  <p className="text-xs text-gray-500 mt-1">{new Date(warning.timestamp).toLocaleTimeString()}</p>
                </div>
              ))
            ) : (
              <div className="px-4 py-3 text-center">
                <p className="text-sm text-green-600 font-medium">✓ No issues detected</p>
                <p className="text-xs text-gray-500 mt-1">Behavior is normal</p>
              </div>
            )}
          </div>
          {warnings.length >= 10 && (
            <div className="bg-red-50 px-4 py-2 text-center">
              <p className="text-red-600 text-sm font-bold">Assessment will auto-submit!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssessmentTaking;
