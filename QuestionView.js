import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from "react-router-dom";

const QuestionView = () => {
    const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchQuestions = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Not authenticated. Please login.');
        return;
      }

      try {
        const response = await axios.get('http://127.0.0.1:8000/api/questions/', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        setQuestions(response.data.questions);
      } catch (err) {
        setError('Failed to fetch questions.');
      }
    };

    fetchQuestions();
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Saved Questions</h2>
      {error && <p className="text-red-600">{error}</p>}
      <ul className="list-disc pl-6 space-y-2">
        {questions.length > 0 ? (
          questions.map((q, index) => (
            <li key={index}>{q.question}</li>
          ))
        ) : (
          <p>No questions found.</p>
        )}
      </ul>
      <button
      onClick={() => navigate(-1)}
      className="bg-black text-white px-4 py-2 rounded mt-4">
      Back
      </button>
    </div>
  );
};

export default QuestionView;
