import React, { useState, useEffect } from 'react';
import { ArrowLeft, FileText, CheckCircle, XCircle, Award, MessageSquare } from 'lucide-react';
import api from '../services/api';

const StudentSubmissionView = ({ submissionId, onBack }) => {
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSubmissionDetails();
  }, [submissionId]);

  const loadSubmissionDetails = async () => {
    try {
      const data = await api.getSubmissionDetails(submissionId);
      setSubmission(data);
    } catch (err) {
      setError(err.message || 'Failed to load submission details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading submission details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 max-w-md text-center shadow-xl">
          <XCircle className="w-16 h-16 text-red-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={onBack}
            className="bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!submission) return null;

  const getScoreColor = (percentage) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-blue-600';
    if (percentage >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const percentage = (submission.total_marks / submission.max_marks) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            <span className="font-semibold">Back to Dashboard</span>
          </button>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Assessment Header */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 mb-2">
                {submission.assessment.title}
              </h1>
              <p className="text-gray-600">
                Submitted on {new Date(submission.submitted_at).toLocaleString()}
              </p>
            </div>
            <div className="text-center">
              <div className={`text-5xl font-bold ${getScoreColor(percentage)} mb-2`}>
                {submission.total_marks.toFixed(1)}
              </div>
              <div className="text-gray-600 text-lg">out of {submission.max_marks}</div>
              <div className={`text-2xl font-semibold ${getScoreColor(percentage)} mt-2`}>
                {percentage.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Overall Teacher Comments */}
          {submission.teacher_comments && (
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border-l-4 border-purple-600 p-6 rounded-lg">
              <div className="flex items-start space-x-3">
                <MessageSquare className="w-6 h-6 text-purple-600 mt-1 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-purple-900 mb-2">Teacher's Overall Comments</h3>
                  <p className="text-gray-800 whitespace-pre-wrap">{submission.teacher_comments}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Question-wise Results */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            <FileText className="w-7 h-7 mr-2 text-indigo-600" />
            Question-wise Results
          </h2>

          {submission.answers.map((answer, index) => {
            const isCorrect = answer.question_type === 'mcq' && 
                            answer.student_answer === answer.correct_answer;
            const answerPercentage = (answer.marks_obtained / answer.max_marks) * 100;

            return (
              <div key={answer.id} className="bg-white rounded-2xl shadow-lg overflow-hidden">
                {/* Question Header */}
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                      <span className="bg-white text-indigo-600 font-bold px-3 py-1 rounded-full">
                        Q{answer.question_number}
                      </span>
                      <span className="text-white font-semibold uppercase text-sm">
                        {answer.question_type}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Award className="w-5 h-5 text-white" />
                      <span className="text-white font-bold text-lg">
                        {answer.marks_obtained.toFixed(1)} / {answer.max_marks}
                      </span>
                      <span className={`ml-2 px-3 py-1 rounded-full text-sm font-semibold ${
                        answerPercentage >= 80 ? 'bg-green-400 text-green-900' :
                        answerPercentage >= 60 ? 'bg-blue-400 text-blue-900' :
                        answerPercentage >= 40 ? 'bg-yellow-400 text-yellow-900' :
                        'bg-red-400 text-red-900'
                      }`}>
                        {answerPercentage.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-6 space-y-4">
                  {/* Question Text */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-500 mb-2">Question</h4>
                    <p className="text-gray-800 text-lg whitespace-pre-wrap">{answer.question_text}</p>
                  </div>

                  {/* Student's Answer */}
                  <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <div className="flex-1">
                        <h4 className="text-sm font-bold text-blue-900 mb-2">Your Answer</h4>
                        <p className="text-gray-800 whitespace-pre-wrap">
                          {answer.student_answer || 'No answer provided'}
                        </p>
                      </div>
                      {answer.question_type === 'mcq' && (
                        <div className="flex-shrink-0">
                          {isCorrect ? (
                            <CheckCircle className="w-6 h-6 text-green-600" />
                          ) : (
                            <XCircle className="w-6 h-6 text-red-600" />
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Correct Answer (for MCQ) */}
                  {answer.question_type === 'mcq' && answer.correct_answer && (
                    <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg">
                      <h4 className="text-sm font-bold text-green-900 mb-2">Correct Answer</h4>
                      <p className="text-gray-800">{answer.correct_answer}</p>
                    </div>
                  )}

                  {/* AI Feedback */}
                  {answer.ai_feedback && (
                    <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded-lg">
                      <h4 className="text-sm font-bold text-purple-900 mb-2 flex items-center">
                        <span className="mr-2">🤖</span>
                        AI Feedback
                      </h4>
                      <p className="text-gray-800 whitespace-pre-wrap">{answer.ai_feedback}</p>
                    </div>
                  )}

                  {/* Teacher's Feedback */}
                  {answer.teacher_feedback && (
                    <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg">
                      <h4 className="text-sm font-bold text-yellow-900 mb-2 flex items-center">
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Teacher's Feedback
                      </h4>
                      <p className="text-gray-800 whitespace-pre-wrap">{answer.teacher_feedback}</p>
                    </div>
                  )}

                  {/* No Feedback Message */}
                  {!answer.teacher_feedback && !answer.ai_feedback && (
                    <div className="bg-gray-50 border-l-4 border-gray-300 p-4 rounded-lg">
                      <p className="text-gray-500 italic">No feedback provided yet</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Summary Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mt-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">Total Questions</p>
              <p className="text-2xl font-bold text-gray-800">{submission.answers.length}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">Score</p>
              <p className={`text-2xl font-bold ${getScoreColor(percentage)}`}>
                {submission.total_marks.toFixed(1)}/{submission.max_marks}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">Percentage</p>
              <p className={`text-2xl font-bold ${getScoreColor(percentage)}`}>
                {percentage.toFixed(1)}%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">Status</p>
              <p className={`text-lg font-bold ${submission.evaluated ? 'text-green-600' : 'text-yellow-600'}`}>
                {submission.evaluated ? 'Evaluated' : 'Pending'}
              </p>
            </div>
          </div>
        </div>

        {/* Back Button */}
        <div className="mt-8 text-center">
          <button
            onClick={onBack}
            className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default StudentSubmissionView;
