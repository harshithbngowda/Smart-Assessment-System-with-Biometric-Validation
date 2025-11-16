import React, { useState, useEffect } from 'react';
import { ArrowLeft, Edit, Save, Eye } from 'lucide-react';
import api from '../services/api';

const ViewSubmissions = ({ assessment, onBack }) => {
  const [submissions, setSubmissions] = useState([]);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState(null);

  useEffect(() => {
    loadSubmissions();
  }, [assessment.id]);

  const loadSubmissions = async () => {
    try {
      const data = await api.getAssessmentSubmissions(assessment.id);
      setSubmissions(data.submissions);
    } catch (err) {
      console.error('Error loading submissions:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewSubmissionDetails = async (submission) => {
    try {
      const data = await api.getSubmissionDetails(submission.id);
      setSelectedSubmission(data);
      setEditData({
        teacher_comments: data.teacher_comments || '',
        answers: data.answers.map(a => ({
          id: a.id,  // Use the actual database ID, not question_number
          marks_obtained: a.marks_obtained || 0,
          teacher_feedback: a.teacher_feedback || ''
        }))
      });
    } catch (err) {
      console.error('Error loading submission details:', err);
    }
  };

  const handleSaveChanges = async () => {
    try {
      await api.updateSubmission(selectedSubmission.id, editData);
      alert('Changes saved successfully!');
      setEditMode(false);
      loadSubmissions();
      viewSubmissionDetails({ id: selectedSubmission.id });
    } catch (err) {
      alert('Error saving changes: ' + err.message);
    }
  };

  const updateAnswerMarks = (answerId, marks) => {
    setEditData({
      ...editData,
      answers: editData.answers.map(a =>
        a.id === answerId ? { ...a, marks_obtained: parseFloat(marks) || 0 } : a
      )
    });
  };

  const updateAnswerFeedback = (answerId, feedback) => {
    setEditData({
      ...editData,
      answers: editData.answers.map(a =>
        a.id === answerId ? { ...a, teacher_feedback: feedback } : a
      )
    });
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">Loading submissions...</p>
      </div>
    );
  }

  if (selectedSubmission) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <button
            onClick={() => setSelectedSubmission(null)}
            className="flex items-center text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Submissions
          </button>
          {!editMode ? (
            <button
              onClick={() => setEditMode(true)}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 flex items-center"
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit Marks
            </button>
          ) : (
            <div className="flex space-x-2">
              <button
                onClick={handleSaveChanges}
                className="bg-green-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-green-700 flex items-center"
              >
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </button>
              <button
                onClick={() => setEditMode(false)}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {/* Student Info */}
        <div className="bg-white rounded-xl p-6 shadow-lg">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Student Information</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Name</p>
              <p className="text-lg font-semibold">{selectedSubmission.student.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Email</p>
              <p className="text-lg">{selectedSubmission.student.email}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Submitted</p>
              <p className="text-lg">{new Date(selectedSubmission.submitted_at).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Score</p>
              <p className="text-2xl font-bold text-purple-600">
                {selectedSubmission.total_marks.toFixed(1)} / {selectedSubmission.max_marks}
              </p>
            </div>
          </div>
        </div>

        {/* Teacher Comments */}
        <div className="bg-white rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-bold text-gray-800 mb-3">Overall Comments</h3>
          {editMode ? (
            <textarea
              value={editData.teacher_comments}
              onChange={(e) => setEditData({ ...editData, teacher_comments: e.target.value })}
              rows={4}
              className="w-full px-4 py-2 rounded-lg border border-gray-300"
              placeholder="Add your comments here..."
            />
          ) : (
            <p className="text-gray-700">
              {selectedSubmission.teacher_comments || 'No comments yet'}
            </p>
          )}
        </div>

        {/* Answers */}
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-gray-800">Answers</h3>
          {selectedSubmission.answers.map((answer, index) => (
            <div key={index} className="bg-white rounded-xl p-6 shadow-lg">
              <div className="mb-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-semibold text-gray-800">
                    Question {answer.question_number}: {answer.question_type.toUpperCase()}
                  </h4>
                  <div className="text-right">
                    {editMode ? (
                      <input
                        type="number"
                        value={editData.answers.find(a => a.id === answer.id)?.marks_obtained || 0}
                        onChange={(e) => updateAnswerMarks(answer.id, e.target.value)}
                        step={0.5}
                        min={0}
                        max={answer.max_marks}
                        className="w-20 px-2 py-1 border border-gray-300 rounded text-right"
                      />
                    ) : (
                      <span className="text-xl font-bold text-purple-600">
                        {answer.marks_obtained.toFixed(1)}
                      </span>
                    )}
                    <span className="text-gray-600"> / {answer.max_marks}</span>
                  </div>
                </div>
                <p className="text-gray-700 mb-3">{answer.question_text}</p>
              </div>

              <div className="space-y-3">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm font-semibold text-blue-900 mb-2">Student's Answer:</p>
                  <p className="text-gray-800 whitespace-pre-wrap">{answer.student_answer || 'No answer provided'}</p>
                </div>

                {answer.question_type === 'mcq' && (
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm font-semibold text-green-900 mb-2">Correct Answer:</p>
                    <p className="text-gray-800">{answer.correct_answer}</p>
                  </div>
                )}

                {answer.ai_feedback && (
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <p className="text-sm font-semibold text-purple-900 mb-2">AI Feedback:</p>
                    <p className="text-gray-800">{answer.ai_feedback}</p>
                  </div>
                )}

                <div className="bg-yellow-50 p-4 rounded-lg">
                  <p className="text-sm font-semibold text-yellow-900 mb-2">Teacher's Feedback:</p>
                  {editMode ? (
                    <textarea
                      value={editData.answers.find(a => a.id === answer.id)?.teacher_feedback || ''}
                      onChange={(e) => updateAnswerFeedback(answer.id, e.target.value)}
                      rows={3}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300"
                      placeholder="Add feedback for this answer..."
                    />
                  ) : (
                    <p className="text-gray-800">{answer.teacher_feedback || 'No feedback yet'}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-gray-800">
          Submissions for: {assessment.title}
        </h3>
        <button
          onClick={onBack}
          className="flex items-center text-gray-600 hover:text-gray-800"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back
        </button>
      </div>

      {submissions.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl">
          <p className="text-gray-500 text-lg">No submissions yet</p>
        </div>
      ) : (
        <div className="space-y-4">
          {submissions.map((submission) => (
            <div
              key={submission.id}
              className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="flex justify-between items-center">
                <div className="flex-1">
                  <h4 className="text-lg font-semibold text-gray-800 mb-2">
                    {submission.student.name}
                  </h4>
                  <p className="text-gray-600 text-sm mb-1">{submission.student.email}</p>
                  <p className="text-gray-500 text-sm">
                    Submitted: {new Date(submission.submitted_at).toLocaleString()}
                  </p>
                  {submission.teacher_comments && (
                    <p className="mt-2 text-sm text-gray-600 italic">
                      Comment: "{submission.teacher_comments}"
                    </p>
                  )}
                </div>
                <div className="text-right ml-6">
                  <div className="text-3xl font-bold text-purple-600 mb-1">
                    {submission.total_marks.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-500 mb-1">
                    out of {submission.max_marks}
                  </div>
                  <div className="text-lg font-semibold text-gray-700 mb-3">
                    {submission.percentage.toFixed(1)}%
                  </div>
                  <button
                    onClick={() => viewSubmissionDetails(submission)}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 flex items-center"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ViewSubmissions;
