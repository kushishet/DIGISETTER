import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from "react-router-dom";

const EditQuestion = () => {
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState('');

  const token = localStorage.getItem('access_token');

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/questions/', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setQuestions(response.data.questions);
    } catch (err) {
      setError('Failed to load questions');
    }
  };

  const deleteQuestion = async (id) => {
    try {
      await axios.delete(`http://127.0.0.1:8000/api/delete/${id}/`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setQuestions(questions.filter(q => q._id !== id));
    } catch (err) {
      setError('Failed to delete question. Admin access required.');
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Questions List</h2>
      {error && <p className="text-red-500">{error}</p>}
      <ul className="space-y-4">
        {questions.map((question) => (
          <li key={question._id} className="border p-4 rounded-md shadow flex justify-between items-center">
            <div>
              <p><strong>Question:</strong> {question.question}</p>
              <p><strong>Marks:</strong> {question.marks}</p>
              <p><strong>Difficulty:</strong> {question.difficulty}</p>
            </div>
            <button
             className="bg-black hover:bg-gray-900 text-white px-4 py-2 rounded shadow"
            onClick={() => deleteQuestion(question._id)}>
            Delete
            </button>
          </li>
        ))}
      </ul>
      <button
      onClick={() => navigate(-1)}
      className="bg-black text-white px-4 py-2 rounded mt-4">
      Back
      </button>
    </div>
  );
};

export default EditQuestion;
