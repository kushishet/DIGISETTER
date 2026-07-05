import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css'; // Custom CSS for styling

const Home = () => {
  return (
    <div className="home-wrapper">
      {/* Navbar */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark px-4 shadow-sm">
    <div className="container-fluid">
    <Link className="navbar-brand text-light" to="/">DIGISETTER</Link>
    <div className="d-flex">
      <Link to="/signup" className="btn btn-outline-light me-2">Signup</Link>
      <Link to="/login" className="btn btn-light">Login</Link>
    </div>
    </div>
    </nav>



      {/* Centered Welcome Section */}
      <div className="home-center">
      <div className="welcome-box p-5 rounded shadow-lg text-center">
        <h1 className="display-5 fw-bold mb-3">Welcome to the DIGISETTER</h1>
        <p className="lead">Upload PDFs or DOCX, generate questions, and build exam papers with ease.</p>
      </div>
      </div>
    </div>
  );
};

export default Home;