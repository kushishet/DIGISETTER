import React, { useState } from 'react';
import API from '../services/api';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await API.post('http://127.0.0.1:8000/api/login/', { username, password });
  
      // Store both tokens
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
     
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid credentials. Please try again.');
    }
  };

  return (
<div className="d-flex justify-content-center mt-5">
  <div className="d-flex shadow-lg" style={{ width: '1100px', borderRadius: '15px', overflow: 'hidden' }}>
    {/* Left - Image */}
    <div style={{ width: '50%' }}>
      <img
        src="https://img.freepik.com/free-vector/hand-drawn-flat-design-innovation-concept_23-2149190151.jpg"
        alt="Visual"
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}/>
    </div>

    {/* Right - Login Form */}
    <div className="p-4" style={{ width: '50%', backgroundColor: '#f9f9f9' }}>
      <h3 className="text-center mb-4">Login</h3>
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleLogin}>
        <div className="form-group mb-3">
          <label>Username</label>
          <input
            type="text"
            className="form-control"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required/>
        </div>
        <div className="form-group mb-4">
          <label>Password</label>
          <input
            type="password"
            className="form-control"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required/>
        </div>
        <button type="submit" className="btn btn-dark w-100">Login</button>
      </form>
    </div>
  </div>
</div>
);
};

export default Login;












