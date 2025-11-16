/**
 * API Service
 * Handles all API calls to the backend
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

class APIService {
  constructor() {
    this.token = localStorage.getItem('token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('token');
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(`${API_URL}${endpoint}`, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Request failed');
      }

      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Authentication
  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async login(credentials) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async adminLogin(credentials) {
    return this.request('/auth/admin/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  // Face Registration
  async registerFace(imageOrImages) {
    const payload = Array.isArray(imageOrImages)
      ? { images: imageOrImages }
      : { image: imageOrImages };
    return this.request('/face/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async verifyFace(imageData) {
    return this.request('/face/verify', {
      method: 'POST',
      body: JSON.stringify({ image: imageData }),
    });
  }

  // Assessment Management (Teacher)
  async createAssessment(assessmentData) {
    return this.request('/assessments', {
      method: 'POST',
      body: JSON.stringify(assessmentData),
    });
  }

  async generateQuestions(data) {
    if (data.file) {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('num_questions', data.num_questions);
      formData.append('mode', data.mode || 'auto');  // Add mode parameter

      const headers = {};
      if (this.token) {
        headers['Authorization'] = `Bearer ${this.token}`;
      }

      const response = await fetch(`${API_URL}/assessments/generate`, {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      const responseData = await response.json();
      if (!response.ok) {
        throw new Error(responseData.error || 'Request failed');
      }
      return responseData;
    } else {
      return this.request('/assessments/generate', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    }
  }

  async getTeacherAssessments() {
    return this.request('/assessments/teacher');
  }

  async getAssessmentDetails(assessmentId) {
    return this.request(`/assessments/${assessmentId}`);
  }

  async getAssessmentSubmissions(assessmentId) {
    return this.request(`/assessments/${assessmentId}/submissions`);
  }

  async updateSubmission(submissionId, data) {
    return this.request(`/submissions/${submissionId}/update`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async convertHandwriting(imageFile) {
    const formData = new FormData();
    formData.append('file', imageFile);

    const headers = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}/handwriting/convert`, {
      method: 'POST',
      headers: headers,
      body: formData,
    });

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error(responseData.error || 'Failed to convert handwriting');
    }
    return responseData;
  }

  // Student
  async accessAssessment(code) {
    return this.request(`/assessments/access/${code}`);
  }

  async submitAssessment(data) {
    return this.request('/submissions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getStudentSubmissions() {
    return this.request('/submissions/student');
  }

  async getSubmissionDetails(submissionId) {
    return this.request(`/submissions/${submissionId}`);
  }

  async deleteSubmission(submissionId) {
    return this.request(`/submissions/${submissionId}`, {
      method: 'DELETE',
    });
  }

  // Admin
  async getAdminStats() {
    return this.request('/admin/stats');
  }

  async getAllUsers() {
    return this.request('/admin/users');
  }

  async getAllAssessments() {
    return this.request('/admin/assessments');
  }

  async createUser(userData) {
    return this.request('/admin/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async updateUser(userId, userData) {
    return this.request(`/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(userId) {
    return this.request(`/admin/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async clearUserFace(userId) {
    return this.request(`/admin/users/${userId}/clear-face`, {
      method: 'POST',
    });
  }

  async adminRegisterFace(userId, imageOrImages) {
    const payload = Array.isArray(imageOrImages)
      ? { images: imageOrImages }
      : { image: imageOrImages };
    return this.request(`/admin/users/${userId}/register-face`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Handwriting to Text
  async convertHandwriting(file) {
    const formData = new FormData();
    formData.append('file', file);

    const headers = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}/handwriting/convert`, {
      method: 'POST',
      headers: headers,
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Request failed');
    }
    return data;
  }

  async monitorCheating(imageData) {
    return this.request('/monitor-cheating', {
      method: 'POST',
      body: JSON.stringify({ image: imageData })
    });
  }

  async evaluateHandwritten(formData) {
    const headers = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}/handwritten-evaluation`, {
      method: 'POST',
      headers: headers,
      body: formData, // Don't set Content-Type, let browser set it with boundary
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Evaluation failed');
    }
    return data;
  }
}

export default new APIService();
