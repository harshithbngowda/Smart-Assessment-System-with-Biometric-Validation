import React, { useState } from 'react';
import { Upload, FileText, Image, CheckCircle, XCircle, ArrowLeft, Loader } from 'lucide-react';
import api from '../services/api';

const HandwrittenEvaluator = ({ user, onBack }) => {
  const [subjectFile, setSubjectFile] = useState(null);
  const [handwrittenFile, setHandwrittenFile] = useState(null);
  const [marksPerQuestion, setMarksPerQuestion] = useState(10);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleSubjectFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const ext = file.name.split('.').pop().toLowerCase();
      if (!['pdf', 'docx', 'txt'].includes(ext)) {
        setError('Subject file must be PDF, DOCX, or TXT');
        return;
      }
      setSubjectFile(file);
      setError('');
    }
  };

  const handleHandwrittenFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const ext = file.name.split('.').pop().toLowerCase();
      if (!['jpg', 'jpeg', 'png', 'pdf'].includes(ext)) {
        setError('Handwritten file must be JPG, PNG, or PDF');
        return;
      }
      setHandwrittenFile(file);
      setError('');
    }
  };

  const handleEvaluate = async () => {
    if (!subjectFile || !handwrittenFile) {
      setError('Please upload both files');
      return;
    }

    setLoading(true);
    setError('');
    setResults(null);

    try {
      const formData = new FormData();
      formData.append('subject_file', subjectFile);
      formData.append('handwritten_file', handwrittenFile);
      formData.append('marks_per_question', marksPerQuestion);

      const data = await api.evaluateHandwritten(formData);
      
      if (data.success) {
        setResults(data);
      } else {
        setError(data.error || 'Evaluation failed');
      }
    } catch (err) {
      setError(err.message || 'Error during evaluation');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSubjectFile(null);
    setHandwrittenFile(null);
    setResults(null);
    setError('');
  };

  const getGradeColor = (percentage) => {
    if (percentage >= 90) return 'text-green-600';
    if (percentage >= 75) return 'text-blue-600';
    if (percentage >= 60) return 'text-yellow-600';
    if (percentage >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getGrade = (percentage) => {
    if (percentage >= 90) return 'A+';
    if (percentage >= 80) return 'A';
    if (percentage >= 70) return 'B+';
    if (percentage >= 60) return 'B';
    if (percentage >= 50) return 'C';
    if (percentage >= 40) return 'D';
    return 'F';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              📝 Handwritten Assessment Evaluator
            </h1>
            <p className="text-gray-600">
              Upload subject content and handwritten answers for AI-powered evaluation
            </p>
          </div>
          <button
            onClick={onBack}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back</span>
          </button>
        </div>

        {!results ? (
          /* Upload Section */
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              {/* Subject Content Upload */}
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 hover:border-purple-400 transition-colors">
                <div className="flex items-center space-x-2 mb-4">
                  <FileText className="w-6 h-6 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-800">
                    Subject Content
                  </h3>
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Upload reference material (PDF, DOCX, or TXT)
                </p>
                <label className="block">
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleSubjectFileChange}
                    className="hidden"
                  />
                  <div className="cursor-pointer bg-purple-50 hover:bg-purple-100 border-2 border-purple-200 rounded-lg p-4 text-center transition-colors">
                    <Upload className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-sm text-purple-700 font-medium">
                      {subjectFile ? subjectFile.name : 'Click to upload'}
                    </p>
                    {subjectFile && (
                      <p className="text-xs text-gray-500 mt-1">
                        {(subjectFile.size / 1024).toFixed(2)} KB
                      </p>
                    )}
                  </div>
                </label>
              </div>

              {/* Handwritten Answers Upload */}
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 hover:border-indigo-400 transition-colors">
                <div className="flex items-center space-x-2 mb-4">
                  <Image className="w-6 h-6 text-indigo-600" />
                  <h3 className="text-lg font-semibold text-gray-800">
                    Handwritten Q&A
                  </h3>
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Upload handwritten questions and answers (JPG, PNG, or PDF)
                </p>
                <label className="block">
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.pdf"
                    onChange={handleHandwrittenFileChange}
                    className="hidden"
                  />
                  <div className="cursor-pointer bg-indigo-50 hover:bg-indigo-100 border-2 border-indigo-200 rounded-lg p-4 text-center transition-colors">
                    <Upload className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
                    <p className="text-sm text-indigo-700 font-medium">
                      {handwrittenFile ? handwrittenFile.name : 'Click to upload'}
                    </p>
                    {handwrittenFile && (
                      <p className="text-xs text-gray-500 mt-1">
                        {(handwrittenFile.size / 1024).toFixed(2)} KB
                      </p>
                    )}
                  </div>
                </label>
              </div>
            </div>

            {/* Marks Per Question */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Marks Per Question
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={marksPerQuestion}
                onChange={(e) => setMarksPerQuestion(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
                <XCircle className="w-5 h-5 text-red-600" />
                <p className="text-red-700">{error}</p>
              </div>
            )}

            {/* Evaluate Button */}
            <button
              onClick={handleEvaluate}
              disabled={loading || !subjectFile || !handwrittenFile}
              className={`w-full py-4 rounded-xl font-semibold text-white transition-all ${
                loading || !subjectFile || !handwrittenFile
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 shadow-lg hover:shadow-xl'
              }`}
            >
              {loading ? (
                <div className="flex items-center justify-center space-x-2">
                  <Loader className="w-5 h-5 animate-spin" />
                  <span>Evaluating... This may take a minute</span>
                </div>
              ) : (
                <div className="flex items-center justify-center space-x-2">
                  <CheckCircle className="w-5 h-5" />
                  <span>Evaluate Answers</span>
                </div>
              )}
            </button>

            {/* Info Box */}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-2">How it works:</h4>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Upload your subject content (notes, textbook, etc.)</li>
                <li>Upload an image of handwritten questions and answers</li>
                <li>AI extracts the handwriting using Gemini Vision</li>
                <li>AI evaluates answers against the subject content</li>
                <li>Get detailed marks and feedback for each question</li>
              </ol>
            </div>
          </div>
        ) : (
          /* Results Section */
          <div className="space-y-6">
            {/* Summary Card */}
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl shadow-lg p-8 text-white">
              <h2 className="text-2xl font-bold mb-6">Evaluation Results</h2>
              <div className="grid md:grid-cols-4 gap-6">
                <div className="bg-white/20 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">Total Questions</p>
                  <p className="text-3xl font-bold">{results.total_questions}</p>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">Score</p>
                  <p className="text-3xl font-bold">
                    {results.total_marks.toFixed(1)}/{results.max_marks}
                  </p>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">Percentage</p>
                  <p className="text-3xl font-bold">{results.percentage.toFixed(1)}%</p>
                </div>
                <div className="bg-white/20 rounded-lg p-4">
                  <p className="text-sm opacity-90 mb-1">Grade</p>
                  <p className="text-3xl font-bold">{getGrade(results.percentage)}</p>
                </div>
              </div>
            </div>

            {/* Detailed Results */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <h3 className="text-xl font-bold text-gray-800 mb-6">Detailed Feedback</h3>
              <div className="space-y-6">
                {results.results.map((result, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <h4 className="text-lg font-semibold text-gray-800">
                        Question {result.question_number}
                      </h4>
                      <div className="text-right">
                        <span className={`text-2xl font-bold ${
                          result.marks_obtained >= result.max_marks * 0.7
                            ? 'text-green-600'
                            : result.marks_obtained >= result.max_marks * 0.5
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}>
                          {result.marks_obtained.toFixed(1)}
                        </span>
                        <span className="text-gray-500">/{result.max_marks}</span>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-1">Question:</p>
                        <p className="text-gray-800">{result.question}</p>
                      </div>

                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-1">Student's Answer:</p>
                        <p className="text-gray-800 bg-gray-50 p-3 rounded-lg">
                          {result.student_answer || '(No answer provided)'}
                        </p>
                      </div>

                      <div>
                        <p className="text-sm font-medium text-gray-600 mb-1">AI Feedback:</p>
                        <p className="text-gray-700 bg-blue-50 p-3 rounded-lg border border-blue-200">
                          {result.feedback}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4">
              <button
                onClick={handleReset}
                className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all"
              >
                Evaluate Another
              </button>
              <button
                onClick={() => window.print()}
                className="flex-1 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold rounded-xl transition-colors"
              >
                Print Results
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HandwrittenEvaluator;
