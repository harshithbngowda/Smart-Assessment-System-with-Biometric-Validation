import React, { useState } from 'react';
import { User, Lock, Mail, BookOpen, Shield } from 'lucide-react';
import api from '../services/api';

const AuthPage = ({ authMode, setAuthMode, portalType, setPortalType, onLogin, onNavigate }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    department: '',
    year: '',
    student_id: '',
    username: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (authMode === 'signup') {
        // Validation
        if (!formData.name || !formData.email || !formData.password) {
          throw new Error('Please fill in all required fields');
        }

        if (formData.password !== formData.confirmPassword) {
          throw new Error('Passwords do not match');
        }

        // Register
        const response = await api.register({
          name: formData.name,
          email: formData.email,
          password: formData.password,
          role: portalType,
          department: formData.department,
          year: formData.year,
          student_id: formData.student_id
        });

        onLogin(response.user, response.access_token, { fromSignup: true });
      } else {
        // Login
        if (portalType === 'admin') {
          const response = await api.adminLogin({
            username: formData.username || formData.email,
            password: formData.password
          });
          onLogin(response.user, response.access_token);
        } else {
          if (!formData.email || !formData.password) {
            throw new Error('Please enter email and password');
          }

          const response = await api.login({
            email: formData.email,
            password: formData.password
          });

          onLogin(response.user, response.access_token);
        }
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-800">
            {authMode === 'login' ? 'Login' : 'Sign Up'}
          </h2>
          <button
            onClick={() => onNavigate('home')}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        <div className="flex space-x-2 mb-6">
          <button
            onClick={() => setPortalType('student')}
            className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
              portalType === 'student'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <User className="w-5 h-5 inline mr-2" />
            Student
          </button>
          <button
            onClick={() => setPortalType('teacher')}
            className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
              portalType === 'teacher'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <BookOpen className="w-5 h-5 inline mr-2" />
            Teacher
          </button>
          <button
            onClick={() => setPortalType('admin')}
            className={`flex-1 py-3 rounded-lg font-semibold transition-all ${
              portalType === 'admin'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Shield className="w-5 h-5 inline mr-2" />
            Admin
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {authMode === 'signup' && portalType !== 'admin' && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Enter your full name"
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none transition-all"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              {portalType === 'admin' ? 'Username' : 'Email'}
            </label>
            <div className="relative">
              <Mail className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" />
              <input
                type={portalType === 'admin' ? 'text' : 'email'}
                name={portalType === 'admin' ? 'username' : 'email'}
                value={portalType === 'admin' ? formData.username : formData.email}
                onChange={handleChange}
                placeholder={portalType === 'admin' ? 'Enter username' : 'Enter your email'}
                className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none transition-all"
                required
              />
            </div>
          </div>

          {authMode === 'signup' && portalType === 'student' && (
            <>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Student ID</label>
                <input
                  type="text"
                  name="student_id"
                  value={formData.student_id}
                  onChange={handleChange}
                  placeholder="Enter your student ID"
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Department</label>
                <input
                  type="text"
                  name="department"
                  value={formData.department}
                  onChange={handleChange}
                  placeholder="e.g., Computer Science"
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Year</label>
                <input
                  type="text"
                  name="year"
                  value={formData.year}
                  onChange={handleChange}
                  placeholder="e.g., 3rd Year"
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none transition-all"
                />
              </div>
            </>
          )}

          {authMode === 'signup' && portalType === 'teacher' && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Department</label>
              <input
                type="text"
                name="department"
                value={formData.department}
                onChange={handleChange}
                placeholder="e.g., Computer Science"
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none transition-all"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
            <div className="relative">
              <Lock className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" />
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none transition-all"
                required
              />
            </div>
          </div>

          {authMode === 'signup' && portalType !== 'admin' && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm Password</label>
              <div className="relative">
                <Lock className="w-5 h-5 text-gray-400 absolute left-3 top-3.5" />
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm your password"
                  className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-600 focus:border-transparent outline-none transition-all"
                  required
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Please wait...' : authMode === 'login' ? 'Login' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}
            className="text-purple-600 hover:text-purple-700 font-semibold"
          >
            {authMode === 'login' 
              ? "Don't have an account? Sign Up" 
              : 'Already have an account? Login'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
