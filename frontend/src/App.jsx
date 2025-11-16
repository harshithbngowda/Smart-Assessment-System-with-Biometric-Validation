import React, { useState, useEffect } from 'react';
import { User, Lock, Mail, BookOpen, Users, Shield, LogOut, BarChart3, FileText, Calendar, Plus, Code, Upload, Eye, Edit, Camera, CheckCircle } from 'lucide-react';
import api from './services/api';

// Import components
import HomePage from './components/HomePage';
import AuthPage from './components/AuthPage';
import StudentDashboard from './components/StudentDashboard';
import TeacherDashboard from './components/TeacherDashboard';
import AdminDashboard from './components/AdminDashboard';
import AssessmentTaking from './components/AssessmentTaking';
import FaceRegistration from './components/FaceRegistration';
import HandwrittenEvaluator from './components/HandwrittenEvaluator';

const AIAssessmentSystem = () => {
  const [currentPage, setCurrentPage] = useState('home');
  const [authMode, setAuthMode] = useState('login');
  const [portalType, setPortalType] = useState('student');
  const [loggedInUser, setLoggedInUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
      try {
        const parsedUser = JSON.parse(user);
        setLoggedInUser(parsedUser);
        api.setToken(token);
        setCurrentPage('dashboard');
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    
    setLoading(false);
  }, []);

  const handleLogin = (user, token, options = {}) => {
    setLoggedInUser(user);
    api.setToken(token);
    localStorage.setItem('user', JSON.stringify(user));
    
    // Only send students to Face Registration right after SIGN UP
    if (options.fromSignup && user.role === 'student') {
      setCurrentPage('face-registration');
      return;
    }
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    setLoggedInUser(null);
    api.clearToken();
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setCurrentPage('home');
  };

  const handleFaceRegistrationComplete = () => {
    // Update user data
    const updatedUser = { ...loggedInUser, has_face_data: true };
    setLoggedInUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
    setCurrentPage('dashboard');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="font-sans">
      {currentPage === 'home' && (
        <HomePage 
          onNavigate={setCurrentPage}
          setAuthMode={setAuthMode}
        />
      )}
      
      {currentPage === 'auth' && (
        <AuthPage 
          authMode={authMode}
          setAuthMode={setAuthMode}
          portalType={portalType}
          setPortalType={setPortalType}
          onLogin={handleLogin}
          onNavigate={setCurrentPage}
        />
      )}

      {currentPage === 'face-registration' && loggedInUser && (
        <FaceRegistration
          user={loggedInUser}
          onComplete={handleFaceRegistrationComplete}
          onSkip={() => setCurrentPage('dashboard')}
        />
      )}

      {currentPage === 'dashboard' && loggedInUser && (
        <>
          {loggedInUser.role === 'student' && (
            <StudentDashboard 
              user={loggedInUser}
              onLogout={handleLogout}
              onNavigate={setCurrentPage}
            />
          )}
          
          {loggedInUser.role === 'teacher' && (
            <TeacherDashboard 
              user={loggedInUser}
              onLogout={handleLogout}
              onNavigate={setCurrentPage}
            />
          )}
          
          {loggedInUser.role === 'admin' && (
            <AdminDashboard 
              user={loggedInUser}
              onLogout={handleLogout}
            />
          )}
        </>
      )}

      {currentPage === 'take-assessment' && loggedInUser && (
        <AssessmentTaking
          user={loggedInUser}
          onComplete={() => setCurrentPage('dashboard')}
          onExit={() => setCurrentPage('dashboard')}
        />
      )}

      {currentPage === 'handwritten-evaluator' && loggedInUser && (
        <HandwrittenEvaluator
          user={loggedInUser}
          onBack={() => setCurrentPage('dashboard')}
        />
      )}
    </div>
  );
};

export default AIAssessmentSystem;
