import React, { useState, useRef, useEffect } from 'react';
import { Camera, CheckCircle, X, RefreshCw, Zap, Users, Shield } from 'lucide-react';
import api from '../services/api';

const FaceRegistration = ({ user, onComplete, onSkip }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [captured, setCaptured] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [autoCapture, setAutoCapture] = useState(false);
  const [captureProgress, setCaptureProgress] = useState(0);
  const [captureStatus, setCaptureStatus] = useState('');
  const [capturedImages, setCapturedImages] = useState([]);

  useEffect(() => {
    startCamera();
    return () => {
      // Cleanup: Stop camera when component unmounts
      stopCamera();
    };
  }, []); // Empty array = run only once on mount

  const startCamera = async () => {
    try {
      console.log('Requesting camera access...');
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false
      });
      console.log('Camera access granted');
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        // For mobile autoplay policies, ensure muted and explicitly play
        videoRef.current.muted = true;
        videoRef.current.playsInline = true;
        // Wait for video metadata to load before playing
        await new Promise((resolve) => {
          videoRef.current.onloadedmetadata = () => {
            console.log('Video metadata loaded, dimensions:', videoRef.current.videoWidth, 'x', videoRef.current.videoHeight);
            resolve();
          };
        });
        await videoRef.current.play().catch(e => console.warn('Play failed:', e));
        console.log('Video playing');
      }
      
      setStream(mediaStream);
      setError('');
    } catch (err) {
      console.error('Camera error:', err);
      const msg = err.name === 'NotAllowedError' 
        ? 'Camera access denied. Please allow camera in browser settings.'
        : err.name === 'NotFoundError'
        ? 'No camera found. Please connect a webcam.'
        : `Camera error: ${err.message}`;
      setError(msg);
      // Ensure any partial tracks are stopped
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
      }
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  };

  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    if (video && canvas) {
      const context = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0);
      
      const imageData = canvas.toDataURL('image/jpeg');
      setCapturedImage(imageData);
      setCaptured(true);
    }
  };

  const retake = () => {
    setCaptured(false);
    setCapturedImage(null);
    setError('');
  };

  const startAutoCapture = async () => {
    try {
      setAutoCapture(true);
      setCapturedImages([]);
      setCaptureProgress(0);
      setCaptureStatus('Initializing camera...');
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas) return;

      const targetFrames = 15; // capture ~15 frames
      const intervalMs = 200; // every 200ms ≈ 3 seconds total

      let frames = [];
      for (let i = 0; i < targetFrames; i++) {
        // draw current frame
        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
        frames.push(dataUrl);
        setCapturedImages(prev => [...prev, dataUrl]);

        // update progress (max 80% during capture)
        const progress = Math.round(((i + 1) / targetFrames) * 80);
        setCaptureProgress(progress);
        setCaptureStatus(`Capturing photos... (${i + 1}/${targetFrames})`);
        // wait interval
        // eslint-disable-next-line no-await-in-loop
        await new Promise(r => setTimeout(r, intervalMs));
      }

      // Send images to backend
      setCaptureStatus('Uploading and processing...');
      setCaptureProgress(90);
      setLoading(true);
      console.log(`[DEBUG] Sending ${frames.length} frames to backend. First frame length: ${frames[0]?.length || 0}`);
      try {
        const resp = await api.registerFace(frames);
        console.log('Face registration response:', resp);
        setCaptureStatus('Finalizing...');
        setCaptureProgress(100);
        setSuccess(true);
        setCaptured(true);
        setCapturedImage(frames[frames.length - 1]);
        setTimeout(() => {
          stopCamera();
          onComplete();
        }, 1200);
      } catch (err) {
        console.error('Face registration error:', err);
        setError(err.message || 'Failed to register face. Please try again.');
        setAutoCapture(false);
        setCaptureProgress(0);
        stopCamera();
      } finally {
        setLoading(false);
      }
    } catch (e) {
      console.error('Auto-capture exception:', e);
      setError('Auto-capture failed. Please try single capture.');
      setAutoCapture(false);
      setCaptureProgress(0);
    }
  };

  const registerFace = async () => {
    if (!capturedImage) return;
    
    setLoading(true);
    setError('');
    
    try {
      console.log('Sending face registration request...');
      const response = await api.registerFace(capturedImage);
      console.log('Face registration response:', response);
      setSuccess(true);
      
      setTimeout(() => {
        stopCamera();
        onComplete();
      }, 2000);
    } catch (err) {
      console.error('Face registration error:', err);
      setError(err.message || 'Failed to register face. Please try again.');
      // Stop camera to avoid it running after failure
      stopCamera();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-2xl">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-purple-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Advanced Face Registration</h2>
          <p className="text-gray-600">
            Multi-photo capture with AI-powered augmentation for maximum security
          </p>
        </div>

        {/* Advanced Features Info */}
        <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
          <div className="flex items-center justify-center space-x-6 text-sm">
            <div className="flex items-center text-purple-700">
              <Zap className="w-4 h-4 mr-1" />
              <span>15+ Photos</span>
            </div>
            <div className="flex items-center text-indigo-700">
              <Users className="w-4 h-4 mr-1" />
              <span>AI Augmentation</span>
            </div>
            <div className="flex items-center text-blue-700">
              <Shield className="w-4 h-4 mr-1" />
              <span>ArcFace Technology</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-center">
            <X className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded-lg flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" />
            Face registered successfully! Redirecting...
          </div>
        )}

        <div className="relative bg-gray-900 rounded-xl overflow-hidden mb-6">
          {!captured ? (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-96 object-cover"
            />
          ) : (
            <img
              src={capturedImage}
              alt="Captured"
              className="w-full h-96 object-cover"
            />
          )}
          
          <canvas ref={canvasRef} className="hidden" />
          
          {/* Guidelines */}
          {!captured && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-64 h-80 border-4 border-white rounded-full opacity-50"></div>
            </div>
          )}
        </div>

        {/* Auto Capture Progress */}
        {autoCapture && (
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">Registration Progress</span>
              <span className="text-sm text-gray-500">{captureProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
              <div 
                className="bg-gradient-to-r from-purple-500 to-indigo-500 h-3 rounded-full transition-all duration-300"
                style={{ width: `${captureProgress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 text-center">{captureStatus}</p>
          </div>
        )}

        <div className="space-y-3">
          {!captured && !autoCapture ? (
            <>
              <button
                onClick={startAutoCapture}
                className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl flex items-center justify-center"
              >
                <Zap className="w-5 h-5 mr-2" />
                Start Advanced Registration
              </button>
              <button
                onClick={capturePhoto}
                className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl flex items-center justify-center"
              >
                <Camera className="w-5 h-5 mr-2" />
                Single Photo Capture
              </button>
              <button
                onClick={onSkip}
                className="w-full bg-gray-200 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-300 transition-all"
              >
                Skip for Now
              </button>
            </>
          ) : !captured && autoCapture ? (
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Registration Progress</span>
                <span className="text-sm text-gray-500">{captureProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-indigo-500 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${captureProgress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 text-center">{captureStatus}</p>
            </div>
          ) : (
            <>
              <button
                onClick={registerFace}
                disabled={loading}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-3 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg hover:shadow-xl flex items-center justify-center disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Registering...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-5 h-5 mr-2" />
                    Confirm & Register
                  </>
                )}
              </button>
              <button
                onClick={retake}
                disabled={loading}
                className="w-full bg-gray-200 text-gray-700 py-3 rounded-lg font-semibold hover:bg-gray-300 transition-all flex items-center justify-center disabled:opacity-50"
              >
                <RefreshCw className="w-5 h-5 mr-2" />
                Retake Photo
              </button>
            </>
          )}
        </div>

        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-800 font-semibold mb-2">
            🚀 Advanced Registration Features:
          </p>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li><strong>Multi-Photo Capture:</strong> Takes 15+ photos automatically</li>
            <li><strong>AI Augmentation:</strong> Creates variations for better accuracy</li>
            <li><strong>ArcFace Technology:</strong> State-of-the-art face recognition</li>
            <li><strong>Anti-Cheating:</strong> Detects multiple faces and phone usage</li>
          </ul>
          
          <div className="mt-3 pt-3 border-t border-blue-200">
            <p className="text-sm text-blue-800 font-semibold">
              💡 Tips for best results:
            </p>
            <ul className="text-sm text-blue-700 mt-1 space-y-1 list-disc list-inside">
              <li>Ensure good lighting on your face</li>
              <li>Look directly at the camera</li>
              <li>Remove glasses if possible</li>
              <li>Keep a neutral expression</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FaceRegistration;
