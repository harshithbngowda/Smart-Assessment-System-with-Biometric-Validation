import React, { useState, useEffect } from 'react';
import { User, Shield, LogOut, FileText, Calendar, Plus, Code, Eye, Trash2 } from 'lucide-react';
import api from '../services/api';
import StudentSubmissionView from './StudentSubmissionView';

const StudentDashboard = ({ user, onLogout, onNavigate }) => {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [assessmentCode, setAssessmentCode] = useState('');
  const [showCodeInput, setShowCodeInput] = useState(false);
  const [error, setError] = useState('');
  const [viewingSubmissionId, setViewingSubmissionId] = useState(null);

  useEffect(() => {
    loadSubmissions();
    
    // Auto-refresh every 5 seconds if there are pending evaluations
    const interval = setInterval(() => {
      if (submissions.some(s => !s.evaluated)) {
        loadSubmissions();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [submissions]);

  const loadSubmissions = async () => {
    try {
      const data = await api.getStudentSubmissions();
      setSubmissions(data.submissions);
    } catch (err) {
      console.error('Error loading submissions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSubmission = async (submissionId, assessmentTitle) => {
    if (!window.confirm(`Are you sure you want to delete your submission for "${assessmentTitle}"? This will allow you to retake the assessment.`)) {
      return;
    }

    try {
      await api.deleteSubmission(submissionId);
      alert('Submission deleted successfully! You can now retake the assessment.');
      loadSubmissions();
    } catch (err) {
      alert('Error deleting submission: ' + err.message);
    }
  };

  const handleAccessAssessment = async () => {
    if (!assessmentCode.trim()) {
      setError('Please enter assessment code');
      return;
    }

    try {
      setError('');
      // Store assessment code for the taking component
      localStorage.setItem('currentAssessmentCode', assessmentCode);
      onNavigate('take-assessment');
    } catch (err) {
      setError(err.message || 'Invalid assessment code');
    }
  };

  const viewSubmissionDetails = (submissionId) => {
    setViewingSubmissionId(submissionId);
  };

  const handleBackFromSubmissionView = () => {
    setViewingSubmissionId(null);
    loadSubmissions(); // Refresh submissions when returning
  };

  // If viewing a specific submission, show the detailed view
  if (viewingSubmissionId) {
    return (
      <StudentSubmissionView
        submissionId={viewingSubmissionId}
        onBack={handleBackFromSubmissionView}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Shield className="w-8 h-8 text-indigo-600" />
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Student Portal
            </span>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center space-x-2 text-gray-600 hover:text-purple-600 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-semibold">Logout</span>
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* User Profile */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="bg-purple-100 p-4 rounded-full">
              <User className="w-12 h-12 text-purple-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{user.name}</h1>
              <p className="text-gray-600">{user.email}</p>
              <div className="mt-2">
                {user.has_face_data ? (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 border border-green-300">
                    Face registered
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-700 border border-yellow-300">
                    Face not registered
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-500 font-semibold">Department</p>
              <p className="text-lg text-gray-800">{user.department || 'Not specified'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 font-semibold">Year</p>
              <p className="text-lg text-gray-800">{user.year || 'Not specified'}</p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Take Assessment */}
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Take Assessment</h2>
          {!showCodeInput ? (
            <button
              onClick={() => setShowCodeInput(true)}
              className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl flex items-center"
            >
              <Plus className="w-5 h-5 mr-2" />
              Enter Assessment Code
            </button>
          ) : (
            <div className="space-y-4">
              {error && (
                <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                  {error}
                </div>
              )}
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={assessmentCode}
                  onChange={(e) => setAssessmentCode(e.target.value.toUpperCase())}
                  placeholder="Enter 8-digit code"
                  maxLength={8}
                  className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none uppercase"
                />
                <button
                  onClick={handleAccessAssessment}
                  className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
                >
                  Start Assessment
                </button>
                <button
                  onClick={() => {
                    setShowCodeInput(false);
                    setAssessmentCode('');
                    setError('');
                  }}
                  className="bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition-all"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
          </div>

          {/* Handwritten Evaluator */}
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">📝 Handwritten Evaluator</h2>
            <p className="text-gray-600 mb-4">
              Upload subject content and handwritten answers for AI-powered evaluation
            </p>
            <button
              onClick={() => onNavigate('handwritten-evaluator')}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg hover:shadow-xl flex items-center w-full justify-center"
            >
              <FileText className="w-5 h-5 mr-2" />
              Open Evaluator
            </button>
          </div>
        </div>

        {/* Assessment Results */}
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="flex items-center space-x-2 mb-6">
            <FileText className="w-6 h-6 text-indigo-600" />
            <h2 className="text-2xl font-bold text-gray-800">My Submissions</h2>
          </div>

          {loading ? (
            <div className="text-center py-8">
              <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Loading submissions...</p>
            </div>
          ) : submissions.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No submissions yet</p>
              <p className="text-gray-400 mt-2">Enter an assessment code above to take your first test</p>
            </div>
          ) : (
            <div className="space-y-4">
              {submissions.map((submission) => (
                <div
                  key={submission.id}
                  className="border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-gray-800 mb-2">
                        {submission.assessment.title}
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-4 h-4" />
                          <span>{new Date(submission.submitted_at).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Shield className={`w-4 h-4 ${submission.evaluated ? 'text-green-600' : 'text-yellow-600 animate-pulse'}`} />
                          <span className={submission.evaluated ? 'text-green-600' : 'text-yellow-600'}>
                            {submission.evaluated ? 'Evaluated' : 'Pending Evaluation (auto-refreshing...)'}
                          </span>
                        </div>
                      </div>
                      {submission.teacher_comments && (
                        <p className="mt-3 text-gray-600 italic">
                          Teacher's comment: "{submission.teacher_comments}"
                        </p>
                      )}
                    </div>
                    <div className="text-right ml-4">
                      <div className="text-3xl font-bold text-purple-600">
                        {submission.total_marks.toFixed(1)}
                      </div>
                      <div className="text-sm text-gray-500">out of {submission.max_marks}</div>
                      <div className="mt-1 text-lg font-semibold text-gray-700">
                        {submission.percentage.toFixed(1)}%
                      </div>
                      <div className="flex flex-col space-y-2 mt-3">
                        {submission.evaluated && (
                          <button
                            onClick={() => viewSubmissionDetails(submission.id)}
                            className="text-indigo-600 hover:text-indigo-800 font-semibold flex items-center text-sm"
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View Details
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteSubmission(submission.id, submission.assessment.title)}
                          className="text-red-600 hover:text-red-800 font-semibold flex items-center text-sm"
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete & Retake
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
