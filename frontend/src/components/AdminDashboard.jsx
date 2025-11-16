import React, { useState, useEffect, useRef } from 'react';
import { Shield, LogOut, Users, BookOpen, FileText, BarChart3, Plus, Edit, Trash2, UserX, Camera } from 'lucide-react';
import api from '../services/api';

const AdminDashboard = ({ user, onLogout }) => {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({ email: '', password: '', name: '', role: 'student', department: '', student_id: '', year: '' });
  const [showFaceModal, setShowFaceModal] = useState(false);
  const [faceRegUser, setFaceRegUser] = useState(null);
  const [capturedFrames, setCapturedFrames] = useState([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsData, usersData, assessmentsData] = await Promise.all([
        api.getAdminStats(),
        api.getAllUsers(),
        api.getAllAssessments()
      ]);
      
      setStats(statsData);
      setUsers(usersData.users);
      setAssessments(assessmentsData.assessments);
    } catch (err) {
      console.error('Error loading admin data:', err);
      alert('Error loading data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const openCreateUser = () => {
    setEditingUser(null);
    setUserForm({ email: '', password: '', name: '', role: 'student', department: '', student_id: '', year: '' });
    setShowUserModal(true);
  };

  const openEditUser = (u) => {
    setEditingUser(u);
    setUserForm({ email: u.email, password: '', name: u.name, role: u.role, department: u.department || '', student_id: u.student_id || '', year: u.year || '' });
    setShowUserModal(true);
  };

  const handleSaveUser = async () => {
    try {
      if (!userForm.email || !userForm.name || !userForm.role) {
        alert('Email, name, and role are required');
        return;
      }
      if (!editingUser && !userForm.password) {
        alert('Password is required for new users');
        return;
      }

      if (editingUser) {
        await api.updateUser(editingUser.id, userForm);
        alert('User updated successfully');
      } else {
        await api.createUser(userForm);
        alert('User created successfully');
      }
      setShowUserModal(false);
      loadData();
    } catch (err) {
      alert('Error saving user: ' + err.message);
    }
  };

  const handleDeleteUser = async (userId, userName) => {
    if (!confirm(`Delete user "${userName}"? This action cannot be undone.`)) return;
    try {
      await api.deleteUser(userId);
      alert('User deleted successfully');
      loadData();
    } catch (err) {
      alert('Error deleting user: ' + err.message);
    }
  };

  const handleClearFace = async (userId, userName) => {
    if (!confirm(`Clear face data for "${userName}"? They will need to re-register.`)) return;
    try {
      await api.clearUserFace(userId);
      alert('Face data cleared successfully');
      loadData();
    } catch (err) {
      alert('Error clearing face data: ' + err.message);
    }
  };

  const openFaceRegistration = async (u) => {
    setFaceRegUser(u);
    setCapturedFrames([]);
    setShowFaceModal(true);
    // Start camera
    setTimeout(async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480, facingMode: 'user' }, audio: false });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
        }
      } catch (err) {
        alert('Camera access denied: ' + err.message);
      }
    }, 100);
  };

  const captureFrame = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.95);
    setCapturedFrames(prev => [...prev, imageData]);
  };

  const startCapture = () => {
    setIsCapturing(true);
    setCapturedFrames([]);
    let count = 0;
    const interval = setInterval(() => {
      captureFrame();
      count++;
      if (count >= 15) {
        clearInterval(interval);
        setIsCapturing(false);
      }
    }, 200);
  };

  const handleSaveFaceData = async () => {
    if (capturedFrames.length < 8) {
      alert('Please capture at least 8 frames (click Start Capture)');
      return;
    }
    try {
      await api.adminRegisterFace(faceRegUser.id, capturedFrames);
      alert('Face registered successfully');
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
      setShowFaceModal(false);
      loadData();
    } catch (err) {
      alert('Error registering face: ' + err.message);
    }
  };

  const closeFaceModal = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
    }
    setShowFaceModal(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Shield className="w-8 h-8 text-indigo-600" />
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Admin Portal
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
        <h1 className="text-3xl font-bold text-gray-800 mb-8">System Overview</h1>
        
        {/* Statistics Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <Users className="w-10 h-10 text-indigo-600" />
              <div className="text-right">
                <div className="text-3xl font-bold text-gray-800">{stats?.total_students || 0}</div>
                <div className="text-sm text-gray-500">Total Students</div>
              </div>
            </div>
            <div className="text-green-600 text-sm font-semibold">Active Users</div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <BookOpen className="w-10 h-10 text-purple-600" />
              <div className="text-right">
                <div className="text-3xl font-bold text-gray-800">{stats?.total_teachers || 0}</div>
                <div className="text-sm text-gray-500">Active Teachers</div>
              </div>
            </div>
            <div className="text-purple-600 text-sm font-semibold">Teaching Staff</div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <FileText className="w-10 h-10 text-pink-600" />
              <div className="text-right">
                <div className="text-3xl font-bold text-gray-800">{stats?.total_assessments || 0}</div>
                <div className="text-sm text-gray-500">Assessments</div>
              </div>
            </div>
            <div className="text-green-600 text-sm font-semibold">{stats?.total_submissions || 0} submissions</div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <Shield className="w-10 h-10 text-rose-600" />
              <div className="text-right">
                <div className="text-3xl font-bold text-gray-800">{stats?.verification_rate || 0}%</div>
                <div className="text-sm text-gray-500">Verification Rate</div>
              </div>
            </div>
            <div className="text-green-600 text-sm font-semibold">Excellent security</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex-1 py-4 px-6 font-semibold transition-colors ${
                activeTab === 'overview'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              System Status
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`flex-1 py-4 px-6 font-semibold transition-colors ${
                activeTab === 'users'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Users ({users.length})
            </button>
            <button
              onClick={() => setActiveTab('assessments')}
              className={`flex-1 py-4 px-6 font-semibold transition-colors ${
                activeTab === 'assessments'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Assessments ({assessments.length})
            </button>
          </div>

          <div className="p-8">
            {activeTab === 'overview' && (
              <div className="space-y-4">
                <h2 className="text-2xl font-bold text-gray-800 mb-6">System Status</h2>
                <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="font-semibold text-gray-800">Assessment Server</span>
                  </div>
                  <span className="text-green-600 font-semibold">Online</span>
                </div>
                <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="font-semibold text-gray-800">Biometric Authentication</span>
                  </div>
                  <span className="text-green-600 font-semibold">Active</span>
                </div>
                <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="font-semibold text-gray-800">Database Connection</span>
                  </div>
                  <span className="text-green-600 font-semibold">Connected</span>
                </div>
                <div className="flex justify-between items-center p-4 bg-purple-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                    <span className="font-semibold text-gray-800">AI Processing Engine</span>
                  </div>
                  <span className="text-purple-600 font-semibold">Running</span>
                </div>
              </div>
            )}

            {activeTab === 'users' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-gray-800">All Users</h2>
                  <button
                    onClick={openCreateUser}
                    className="flex items-center space-x-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <Plus className="w-5 h-5" />
                    <span>Add User</span>
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b-2 border-gray-200">
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Name</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Email</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Role</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Department</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Face Data</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.id} className="border-b border-gray-100 hover:bg-purple-50 transition-colors">
                          <td className="py-4 px-4 text-gray-800 font-medium">{u.name}</td>
                          <td className="py-4 px-4 text-gray-600">{u.email}</td>
                          <td className="py-4 px-4">
                            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                              u.role === 'teacher' ? 'bg-purple-100 text-purple-800' :
                              u.role === 'admin' ? 'bg-red-100 text-red-800' :
                              u.role === 'student' ? 'bg-blue-100 text-blue-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {u.role}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-gray-600">{u.department || 'N/A'}</td>
                          <td className="py-4 px-4">
                            {u.has_face_data ? (
                              <span className="text-green-600 font-semibold">✓ Registered</span>
                            ) : (
                              <span className="text-gray-400">Not registered</span>
                            )}
                          </td>
                          <td className="py-4 px-4">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => openEditUser(u)}
                                className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                title="Edit user"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => openFaceRegistration(u)}
                                className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                title="Register/Re-register face"
                              >
                                <Camera className="w-4 h-4" />
                              </button>
                              {u.has_face_data && (
                                <button
                                  onClick={() => handleClearFace(u.id, u.name)}
                                  className="p-2 text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                                  title="Clear face data"
                                >
                                  <UserX className="w-4 h-4" />
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteUser(u.id, u.name)}
                                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                title="Delete user"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'assessments' && (
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-6">All Assessments</h2>
                <div className="space-y-4">
                  {assessments.map((assessment) => (
                    <div key={assessment.id} className="border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="text-xl font-semibold text-gray-800 mb-2">{assessment.title}</h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span>Code: <strong>{assessment.code}</strong></span>
                            <span>Teacher: {assessment.teacher.name}</span>
                            <span className="text-purple-600 font-semibold">
                              {assessment.submissions_count} submissions
                            </span>
                          </div>
                          <p className="text-gray-500 text-sm mt-2">
                            Created: {new Date(assessment.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Face Registration Modal */}
      {showFaceModal && faceRegUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6">
            <h3 className="text-2xl font-bold text-gray-800 mb-4">
              Register Face for {faceRegUser.name}
            </h3>
            <div className="space-y-4">
              <div className="bg-gray-100 rounded-lg overflow-hidden" style={{ height: '360px' }}>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Captured: <span className="font-bold text-purple-600">{capturedFrames.length}/15</span> frames
                </div>
                <button
                  onClick={startCapture}
                  disabled={isCapturing}
                  className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
                    isCapturing
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-purple-600 text-white hover:bg-purple-700'
                  }`}
                >
                  {isCapturing ? 'Capturing...' : 'Start Capture'}
                </button>
              </div>
              <p className="text-sm text-gray-600">
                💡 Tip: Ensure good lighting and look at the camera from different angles during capture.
              </p>
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={closeFaceModal}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveFaceData}
                disabled={capturedFrames.length < 8}
                className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-colors ${
                  capturedFrames.length < 8
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                Save Face Data
              </button>
            </div>
          </div>
        </div>
      )}

      {/* User Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-2xl font-bold text-gray-800 mb-6">
              {editingUser ? 'Edit User' : 'Create New User'}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Email *</label>
                <input
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                  placeholder="user@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Password {editingUser ? '(leave blank to keep current)' : '*'}
                </label>
                <input
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                  placeholder="Enter password"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Name *</label>
                <input
                  type="text"
                  value={userForm.name}
                  onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                  placeholder="Full name"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Role *</label>
                <select
                  value={userForm.role}
                  onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                >
                  <option value="student">Student</option>
                  <option value="teacher">Teacher</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Department</label>
                <input
                  type="text"
                  value={userForm.department}
                  onChange={(e) => setUserForm({ ...userForm, department: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                  placeholder="e.g., Computer Science"
                />
              </div>
              {userForm.role === 'student' && (
                <>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Student ID</label>
                    <input
                      type="text"
                      value={userForm.student_id}
                      onChange={(e) => setUserForm({ ...userForm, student_id: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                      placeholder="e.g., 2021001"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Year</label>
                    <input
                      type="text"
                      value={userForm.year}
                      onChange={(e) => setUserForm({ ...userForm, year: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent"
                      placeholder="e.g., 2nd Year"
                    />
                  </div>
                </>
              )}
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowUserModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveUser}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-semibold"
              >
                {editingUser ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
