import React from 'react';
import { Shield, BarChart3, Users } from 'lucide-react';

const HomePage = ({ onNavigate, setAuthMode }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50">
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Shield className="w-8 h-8 text-indigo-600" />
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              AI Assessment
            </span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <h1 className="text-5xl font-bold text-gray-800 leading-tight">
              AI Assessment System using{' '}
              <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                Biometric Verification
              </span>
            </h1>
            <p className="text-lg text-gray-600 leading-relaxed">
              Our cutting-edge AI Assessment System revolutionizes the way educational institutions conduct student evaluations. 
              By integrating advanced biometric verification technology, we ensure secure, authentic, and automated assessments 
              that maintain academic integrity while providing real-time results and comprehensive analytics.
            </p>
            <p className="text-lg text-gray-600 leading-relaxed">
              The system leverages artificial intelligence to analyze responses, detect patterns, and provide instant feedback, 
              while biometric authentication guarantees that each assessment is taken by the registered student, eliminating 
              impersonation and ensuring fair evaluation for all participants.
            </p>
            <div className="flex items-center space-x-4 pt-4">
              <div className="flex items-center space-x-2 text-indigo-600">
                <Shield className="w-5 h-5" />
                <span className="font-semibold">Secure</span>
              </div>
              <div className="flex items-center space-x-2 text-purple-600">
                <BarChart3 className="w-5 h-5" />
                <span className="font-semibold">Automated</span>
              </div>
              <div className="flex items-center space-x-2 text-pink-600">
                <Users className="w-5 h-5" />
                <span className="font-semibold">Scalable</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-2xl p-8 space-y-6">
            <h2 className="text-3xl font-bold text-gray-800 text-center">Get Started</h2>
            <p className="text-gray-600 text-center">Access your portal to begin assessments</p>
            <div className="space-y-4">
              <button
                onClick={() => {
                  setAuthMode('login');
                  onNavigate('auth');
                }}
                className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-4 rounded-xl font-semibold text-lg hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                Login
              </button>
              <button
                onClick={() => {
                  setAuthMode('signup');
                  onNavigate('auth');
                }}
                className="w-full bg-white text-purple-600 py-4 rounded-xl font-semibold text-lg border-2 border-purple-600 hover:bg-purple-50 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                Sign Up
              </button>
            </div>
            <div className="pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-500 text-center">
                Secure authentication with biometric verification
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
