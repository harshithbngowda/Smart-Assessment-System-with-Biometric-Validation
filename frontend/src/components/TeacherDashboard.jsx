import React, { useState, useEffect } from 'react';
import { BookOpen, Shield, LogOut, Plus, Upload, FileText, Users, Eye, Edit, Code, FileQuestion } from 'lucide-react';
import api from '../services/api';
import CreateAssessment from './CreateAssessment';
import ViewSubmissions from './ViewSubmissions';

const TeacherDashboard = ({ user, onLogout, onNavigate }) => {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('assessments'); // 'assessments', 'create', 'view-submissions'
  const [selectedAssessment, setSelectedAssessment] = useState(null);

  useEffect(() => {
    loadAssessments();
  }, []);

  const loadAssessments = async () => {
    try {
      const data = await api.getTeacherAssessments();
      setAssessments(data.assessments);
    } catch (err) {
      console.error('Error loading assessments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAssessmentCreated = () => {
    setActiveTab('assessments');
    loadAssessments();
  };

  const viewSubmissions = (assessment) => {
    setSelectedAssessment(assessment);
    setActiveTab('view-submissions');
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    alert(`Assessment code ${code} copied to clipboard!`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Shield className="w-8 h-8 text-indigo-600" />
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Teacher Portal
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
        {/* Profile Section */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <div className="flex items-center space-x-4 mb-6">
            <div className="bg-purple-100 p-4 rounded-full">
              <BookOpen className="w-12 h-12 text-purple-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{user.name}</h1>
              <p className="text-gray-600">{user.email}</p>
            </div>
          </div>
          <div>
            <p className="text-sm text-gray-500 font-semibold">Department</p>
            <p className="text-lg text-gray-800">{user.department || 'Not specified'}</p>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
            <FileText className="w-10 h-10 mb-3 opacity-80" />
            <div className="text-4xl font-bold mb-1">{assessments.length}</div>
            <div className="text-indigo-100">Total Assessments</div>
          </div>
          <div className="bg-gradient-to-br from-pink-500 to-rose-600 rounded-2xl shadow-lg p-6 text-white">
            <Users className="w-10 h-10 mb-3 opacity-80" />
            <div className="text-4xl font-bold mb-1">
              {assessments.reduce((sum, a) => sum + a.submissions_count, 0)}
            </div>
            <div className="text-pink-100">Total Submissions</div>
          </div>
          <div className="bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
            <Shield className="w-10 h-10 mb-3 opacity-80" />
            <div className="text-4xl font-bold mb-1">100%</div>
            <div className="text-purple-100">Security Active</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-t-2xl shadow-lg">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('assessments')}
              className={`flex-1 py-4 px-6 font-semibold transition-colors ${
                activeTab === 'assessments'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <FileText className="w-5 h-5 inline mr-2" />
              My Assessments
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={`flex-1 py-4 px-6 font-semibold transition-colors ${
                activeTab === 'create'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <Plus className="w-5 h-5 inline mr-2" />
              Create Assessment
            </button>
            <button
              onClick={() => onNavigate('handwritten-evaluator')}
              className="flex-1 py-4 px-6 font-semibold text-gray-600 hover:text-gray-800 transition-colors"
            >
              <FileQuestion className="w-5 h-5 inline mr-2" />
              Handwritten Evaluator
            </button>
          </div>

          <div className="p-8">
            {activeTab === 'assessments' && (
              <div>
                {loading ? (
                  <div className="text-center py-8">
                    <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading assessments...</p>
                  </div>
                ) : assessments.length === 0 ? (
                  <div className="text-center py-12">
                    <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">No assessments created yet</p>
                    <button
                      onClick={() => setActiveTab('create')}
                      className="mt-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg"
                    >
                      Create Your First Assessment
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {assessments.map((assessment) => (
                      <div
                        key={assessment.id}
                        className="border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="text-xl font-semibold text-gray-800 mb-2">
                              {assessment.title}
                            </h3>
                            {assessment.description && (
                              <p className="text-gray-600 mb-3">{assessment.description}</p>
                            )}
                            <div className="flex items-center space-x-4 text-sm text-gray-600">
                              <span>Duration: {assessment.duration_minutes} mins</span>
                              <span>Total Marks: {assessment.total_marks}</span>
                              <span className="text-purple-600 font-semibold">
                                {assessment.submissions_count} submissions
                              </span>
                            </div>
                            <div className="mt-3 flex items-center space-x-2">
                              <span className="text-sm text-gray-600">Assessment Code:</span>
                              <code className="bg-gray-100 px-3 py-1 rounded text-lg font-mono font-bold text-purple-600">
                                {assessment.code}
                              </code>
                              <button
                                onClick={() => copyCode(assessment.code)}
                                className="text-indigo-600 hover:text-indigo-800 text-sm font-semibold"
                              >
                                Copy
                              </button>
                            </div>
                          </div>
                          <div className="ml-4 flex flex-col space-y-2">
                            <button
                              onClick={() => viewSubmissions(assessment)}
                              className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 transition-all flex items-center whitespace-nowrap"
                            >
                              <Eye className="w-4 h-4 mr-2" />
                              View Submissions
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'create' && (
              <CreateAssessment onSuccess={handleAssessmentCreated} />
            )}

            {activeTab === 'view-submissions' && selectedAssessment && (
              <ViewSubmissions
                assessment={selectedAssessment}
                onBack={() => setActiveTab('assessments')}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;
