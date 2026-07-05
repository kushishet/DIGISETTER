import React, { useState } from 'react';
import { useNavigate } from "react-router-dom";


const InsertQuestion = () => {
    const navigate = useNavigate();
  // State to store the form data
  const [questionData, setQuestionData] = useState({
    question: '',
    subject: '',
    difficulty: 'easy', // Default difficulty
    marks: 0, // Default marks
  });

  // State to manage error/success messages
  const [message, setMessage] = useState('');

  // Handle changes to the input fields
  const handleChange = (e) => {
    const { name, value } = e.target;
    setQuestionData({ ...questionData, [name]: value });
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prepare the data to send to the backend
    const dataToSend = {
      question: questionData.question,
      subject: questionData.subject,
      difficulty: questionData.difficulty,
      marks: questionData.marks,
    };

    try {
      // Send POST request to the backend API
      const response = await fetch('http://127.0.0.1:8000/api/insert/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,

        },
        body: JSON.stringify(dataToSend),
      });

      // Check if the request was successful
      if (response.ok) {
        const result = await response.json();
        setMessage({ type: 'success', text: result.message });
        setQuestionData({
          question: '',
          subject: '',
          difficulty: 'easy',
          marks: 0,
        }); // Reset the form
      } else {
        const errorResult = await response.json();
        setMessage({ type: 'error', text: errorResult.error || 'An error occurred' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'An error occurred' });
    }
  };

  return (
    <div className="container mt-5">
      <h2 className="mb-4">Insert Question</h2>
  
      {message && (
        <div className={`alert alert-${message.type === 'error' ? 'danger' : 'success'}`} role="alert">
        {message.text}
        </div>
      )}
  
      <form onSubmit={handleSubmit}>
        {/* Question input */}
        <div className="mb-3">
          <label htmlFor="question" className="form-label">Question</label>
          <input
            type="text"
            className="form-control"
            id="question"
            name="question"
            value={questionData.question}
            onChange={handleChange}
            required/>
        </div>
  
        {/* Subject input */}
        <div className="mb-3">
          <label htmlFor="subject" className="form-label">Subject</label>
          <input
            type="text"
            className="form-control"
            id="subject"
            name="subject"
            value={questionData.subject}
            onChange={handleChange}
            required/>
        </div>
  
        {/* Difficulty input */}
        <div className="mb-3">
          <label htmlFor="difficulty" className="form-label">Difficulty</label>
          <select
            className="form-control"
            id="difficulty"
            name="difficulty"
            value={questionData.difficulty}
            onChange={handleChange}
            required>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
  
        {/* Marks input */}
        <div className="mb-3">
          <label htmlFor="marks" className="form-label">Marks</label>
          <input
            type="number"
            className="form-control"
            id="marks"
            name="marks"
            value={questionData.marks}
            onChange={handleChange}
            required
            min="1"/>
        </div>
  
        <button type="submit" className="btn btn-dark">
        Add Question
        </button>
      </form>
      <button
      onClick={() => navigate(-1)}
      className="bg-black text-white px-4 py-2 rounded mt-4">
      Back
      </button>
    </div>
  );
}  

export default InsertQuestion;
