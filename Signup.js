import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Signup = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:8000/api/signup/', {
        username,
        email,
        password
      });
      alert('Signup successful!');
      navigate('/login');
    } catch (error) {
      alert('Signup failed: ' + error.response.data.error);
    }
  };

  return (
    <div className="container mt-5">
      <div className="row shadow-lg rounded overflow-hidden">
        {/* Left side - Image */}
        <div className="col-md-6 p-0">
          <img
            src="https://www.ashaclasses.in/wp-content/uploads/2024/03/ae.png"
            alt="Signup visual"
            className="img-fluid h-100 w-100 object-fit-cover"
            style={{ objectFit: 'cover', height: '100%' }}
          />
        </div>

        {/* Right side - Signup form */}
        <div className="col-md-6 p-5 bg-light">
          <h2 className="mb-4">Sign-up</h2>
          <form onSubmit={handleSignup}>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              className="form-control mb-3"
              required/>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              className="form-control mb-3"
              required/>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="form-control mb-4"
              required/>
            <button type="submit" className="btn btn-dark w-100">
            Signup
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Signup;
