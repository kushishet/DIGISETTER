import axios from 'axios';
const API = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
});

// Add interceptor to attach the token
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');

  // Avoid attaching token to login or signup
  if (
    !config.url.includes('/login') &&
    !config.url.includes('/signup') &&
    token
  ) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export const uploadPDF = async (formData) => {
  return API.post('/upload-pdf/', formData);
};
export const uploadDOCX = async (formData) => {
  return API.post('/upload-docx/', formData);
};

export const insertData = async (dataToSend) => {
  try {
    const response = await API.post('/insert/', dataToSend);
    return response.data; // Return the response data
  } catch (error) {
    console.error('Insert failed:', error);
    throw error; // Rethrow error to handle it later
  }
};
export default API;
