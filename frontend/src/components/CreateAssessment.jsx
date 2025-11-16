import React, { useState } from 'react';
import { Plus, Trash2, Upload, FileText, Wand2, Save } from 'lucide-react';
import api from '../services/api';

const CreateAssessment = ({ onSuccess }) => {
  const [step, setStep] = useState(1); // 1: Details, 2: Questions, 3: Review
  const [assessmentData, setAssessmentData] = useState({
    title: '',
    description: '',
    duration_minutes: 60,
  });
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generateMode, setGenerateMode] = useState(null); // 'file', 'text', 'handwriting', or null

  // Question generation
  const [genFile, setGenFile] = useState(null);
  const [genText, setGenText] = useState('');
  const [genHandwriting, setGenHandwriting] = useState(null);
  const [numQuestions, setNumQuestions] = useState(10);
  const [questionMode, setQuestionMode] = useState('mixed'); // 'mixed', 'mcq', 'descriptive', 'programming'

  const handleGenerateQuestions = async () => {
    setLoading(true);
    setError('');

    try {
      let data;
      if (generateMode === 'file' && genFile) {
        data = await api.generateQuestions({
          file: genFile,
          num_questions: numQuestions,
          mode: questionMode,
        });
      } else if (generateMode === 'handwriting' && genHandwriting) {
        // First convert handwriting to text
        const convertData = await api.convertHandwriting(genHandwriting);
        // Then generate questions from the converted text
        data = await api.generateQuestions({
          text: convertData.text,
          num_questions: numQuestions,
          mode: questionMode,
        });
      } else if (generateMode === 'text' && genText.trim()) {
        data = await api.generateQuestions({
          text: genText,
          num_questions: numQuestions,
          mode: questionMode,
        });
      } else {
        throw new Error('Please provide file, handwriting image, or text');
      }

      // Add generated questions
      setQuestions([...questions, ...data.questions]);
      setGenerateMode(null);
      setGenFile(null);
      setGenText('');
      setGenHandwriting(null);
      alert(`${data.questions.length} questions generated successfully!`);
    } catch (err) {
      setError(err.message || 'Failed to generate questions');
    } finally {
      setLoading(false);
    }
  };

  const addManualQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_text: '',
        question_type: 'descriptive',
        correct_answer: '',
        marks: 10,
        options: ['', '', '', ''],
      },
    ]);
  };

  const updateQuestion = (index, field, value) => {
    const updated = [...questions];
    updated[index][field] = value;
    setQuestions(updated);
  };

  const updateOption = (qIndex, optIndex, value) => {
    const updated = [...questions];
    updated[qIndex].options[optIndex] = value;
    setQuestions(updated);
  };

  const removeQuestion = (index) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    // Validation
    if (!assessmentData.title.trim()) {
      setError('Please enter assessment title');
      return;
    }

    if (questions.length === 0) {
      setError('Please add at least one question');
      return;
    }

    // Validate questions
    for (let i = 0; i < questions.length; i++) {
      const q = questions[i];
      if (!q.question_text.trim()) {
        setError(`Question ${i + 1} is empty`);
        return;
      }
      if (q.question_type === 'mcq' && (!q.options || q.options.some(o => !o.trim()))) {
        setError(`Question ${i + 1}: All MCQ options must be filled`);
        return;
      }
    }

    setLoading(true);
    setError('');

    try {
      await api.createAssessment({
        ...assessmentData,
        questions: questions,
      });
      
      alert('Assessment created successfully!');
      onSuccess();
    } catch (err) {
      setError(err.message || 'Failed to create assessment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Step 1: Assessment Details */}
      {step === 1 && (
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-gray-800">Assessment Details</h3>
          
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Assessment Title *
            </label>
            <input
              type="text"
              value={assessmentData.title}
              onChange={(e) =>
                setAssessmentData({ ...assessmentData, title: e.target.value })
              }
              placeholder="e.g., Data Structures Final Exam"
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={assessmentData.description}
              onChange={(e) =>
                setAssessmentData({ ...assessmentData, description: e.target.value })
              }
              placeholder="Brief description of the assessment"
              rows={3}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Duration (minutes)
            </label>
            <input
              type="number"
              value={assessmentData.duration_minutes}
              onChange={(e) =>
                setAssessmentData({
                  ...assessmentData,
                  duration_minutes: parseInt(e.target.value),
                })
              }
              min={1}
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none"
            />
          </div>

          <button
            onClick={() => setStep(2)}
            className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
          >
            Next: Add Questions
          </button>
        </div>
      )}

      {/* Step 2: Add Questions */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-bold text-gray-800">
              Questions ({questions.length})
            </h3>
            <button
              onClick={() => setStep(1)}
              className="text-gray-600 hover:text-gray-800"
            >
              ← Back to Details
            </button>
          </div>

          {/* Generate Questions Section */}
          <div className="bg-purple-50 rounded-xl p-6 space-y-4">
            <h4 className="font-semibold text-gray-800 flex items-center">
              <Wand2 className="w-5 h-5 mr-2 text-purple-600" />
              Auto-Generate Questions
            </h4>

            <div className="grid grid-cols-3 gap-4">
              <button
                onClick={() => setGenerateMode('file')}
                className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                  generateMode === 'file'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Upload className="w-5 h-5 inline mr-2" />
                Upload File
              </button>
              <button
                onClick={() => setGenerateMode('handwriting')}
                className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                  generateMode === 'handwriting'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <FileText className="w-5 h-5 inline mr-2" />
                Handwritten Notes
              </button>
              <button
                onClick={() => setGenerateMode('text')}
                className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
                  generateMode === 'text'
                    ? 'bg-purple-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <FileText className="w-5 h-5 inline mr-2" />
                Enter Text
              </button>
            </div>

            {generateMode === 'file' && (
              <div>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setGenFile(e.target.files[0])}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 bg-white"
                />
                <p className="text-sm text-gray-600 mt-2">
                  Supported formats: PDF, DOCX, TXT
                </p>
              </div>
            )}

            {generateMode === 'handwriting' && (
              <div>
                <input
                  type="file"
                  accept="image/*,.pdf"
                  onChange={(e) => setGenHandwriting(e.target.files[0])}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 bg-white"
                />
                <p className="text-sm text-gray-600 mt-2">
                  📝 Upload handwritten notes (JPG, PNG, PDF, etc.) - AI will convert to text and generate questions
                </p>
              </div>
            )}

            {generateMode === 'text' && (
              <textarea
                value={genText}
                onChange={(e) => setGenText(e.target.value)}
                placeholder="Paste your content here..."
                rows={6}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 outline-none"
              />
            )}

            {generateMode && (
              <>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Question Type
                  </label>
                  <div className="grid grid-cols-4 gap-2">
                    <button
                      onClick={() => setQuestionMode('mixed')}
                      className={`py-2 px-3 rounded-lg font-semibold text-sm transition-all ${
                        questionMode === 'mixed'
                          ? 'bg-purple-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                      }`}
                    >
                      Mixed
                    </button>
                    <button
                      onClick={() => setQuestionMode('descriptive')}
                      className={`py-2 px-3 rounded-lg font-semibold text-sm transition-all ${
                        questionMode === 'descriptive'
                          ? 'bg-purple-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                      }`}
                    >
                      Descriptive
                    </button>
                    <button
                      onClick={() => setQuestionMode('mcq')}
                      className={`py-2 px-3 rounded-lg font-semibold text-sm transition-all ${
                        questionMode === 'mcq'
                          ? 'bg-purple-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                      }`}
                    >
                      MCQ
                    </button>
                    <button
                      onClick={() => setQuestionMode('programming')}
                      className={`py-2 px-3 rounded-lg font-semibold text-sm transition-all ${
                        questionMode === 'programming'
                          ? 'bg-purple-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                      }`}
                    >
                      Programming
                    </button>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    {questionMode === 'auto' && 'Automatically detects content type and generates appropriate questions'}
                    {questionMode === 'descriptive' && 'Generates analytical 10-mark descriptive questions'}
                    {questionMode === 'mcq' && 'Generates multiple choice questions with 4 options'}
                    {questionMode === 'programming' && 'Generates "Write a program to..." questions with full working code'}
                  </p>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Number of Questions
                    </label>
                    <input
                      type="number"
                      value={numQuestions}
                      onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                      min={1}
                      max={50}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300"
                    />
                  </div>
                <div className="flex space-x-2">
                  <button
                    onClick={handleGenerateQuestions}
                    disabled={loading}
                    className="bg-purple-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-purple-700 transition-all disabled:opacity-50 whitespace-nowrap"
                  >
                    {loading ? 'Generating...' : 'Generate'}
                  </button>
                  <button
                    onClick={() => {
                      setGenerateMode(null);
                      setGenFile(null);
                      setGenText('');
                    }}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                </div>
              </div>
              </>
            )}
          </div>

          {/* Manual Question Entry */}
          <div>
            <button
              onClick={addManualQuestion}
              className="bg-white border-2 border-dashed border-purple-300 text-purple-600 px-6 py-3 rounded-lg font-semibold hover:border-purple-400 hover:bg-purple-50 transition-all flex items-center"
            >
              <Plus className="w-5 h-5 mr-2" />
              Add Question Manually
            </button>
          </div>

          {/* Questions List */}
          <div className="space-y-4">
            {questions.map((q, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-xl p-6">
                <div className="flex justify-between items-start mb-4">
                  <h4 className="font-semibold text-gray-800">Question {index + 1}</h4>
                  <button
                    onClick={() => removeQuestion(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Question Type
                    </label>
                    <select
                      value={q.question_type}
                      onChange={(e) => updateQuestion(index, 'question_type', e.target.value)}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300"
                    >
                      <option value="mcq">Multiple Choice</option>
                      <option value="descriptive">Descriptive</option>
                      <option value="programming">Programming</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Question Text
                    </label>
                    <textarea
                      value={q.question_text}
                      onChange={(e) => updateQuestion(index, 'question_text', e.target.value)}
                      rows={3}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300"
                      placeholder="Enter your question..."
                    />
                  </div>

                  {q.question_type === 'mcq' && (
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Options
                      </label>
                      {q.options.map((opt, optIndex) => (
                        <input
                          key={optIndex}
                          type="text"
                          value={opt}
                          onChange={(e) => updateOption(index, optIndex, e.target.value)}
                          placeholder={`Option ${String.fromCharCode(65 + optIndex)}`}
                          className="w-full px-4 py-2 rounded-lg border border-gray-300 mb-2"
                        />
                      ))}
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Correct Answer
                        </label>
                        <select
                          value={q.correct_answer}
                          onChange={(e) => updateQuestion(index, 'correct_answer', e.target.value)}
                          className="w-full px-4 py-2 rounded-lg border border-gray-300"
                        >
                          <option value="">Select correct option</option>
                          <option value="A">A</option>
                          <option value="B">B</option>
                          <option value="C">C</option>
                          <option value="D">D</option>
                        </select>
                      </div>
                    </div>
                  )}

                  {q.question_type !== 'mcq' && (
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Model Answer / Key Points
                      </label>
                      <textarea
                        value={q.correct_answer}
                        onChange={(e) => updateQuestion(index, 'correct_answer', e.target.value)}
                        rows={4}
                        className="w-full px-4 py-2 rounded-lg border border-gray-300"
                        placeholder="Enter the model answer or key points for evaluation..."
                      />
                    </div>
                  )}

                  <div className="w-32">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Marks
                    </label>
                    <input
                      type="number"
                      value={q.marks}
                      onChange={(e) => updateQuestion(index, 'marks', parseFloat(e.target.value))}
                      min={0.5}
                      step={0.5}
                      className="w-full px-4 py-2 rounded-lg border border-gray-300"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {questions.length > 0 && (
            <div className="flex justify-between items-center pt-4 border-t">
              <div className="text-gray-600">
                Total: {questions.length} questions, {questions.reduce((sum, q) => sum + q.marks, 0)} marks
              </div>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg flex items-center disabled:opacity-50"
              >
                <Save className="w-5 h-5 mr-2" />
                {loading ? 'Creating...' : 'Create Assessment'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CreateAssessment;
