import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const McqBased = () => {
    const navigate = useNavigate();
  const [formData, setFormData] = useState({
    subject: "",
    prompt: "",
    num_questions: 10,
    difficulty: "medium"
  });

  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [pdfUrl, setPdfUrl] = useState("");
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setQuestions([]);
    setPdfUrl("");

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/generate-mcqs/", formData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });

      setQuestions(res.data.questions);
      setPdfUrl(res.data.pdf_url);
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
   <div className="min-h-screen bg-cover bg-center flex items-center justify-center">
    <div className="container max-w-2xl p-6 shadow-lg rounded" style={{ backgroundColor: "rgba(255, 255, 255, 0.1)", border: "1px solid #ccc" }}>
      <h2 className="text-2xl font-bold mb-4 text-center">Generating Mcq From Prompt </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          name="subject"
          placeholder="Subject"
          className="w-full p-2 border rounded"
          value={formData.subject}
          onChange={handleChange}
          required/>
        <input
          type="text"
          name="prompt"
          placeholder="Topic Prompt"
          className="w-full p-2 border rounded"
          value={formData.prompt}
          onChange={handleChange}
          required/>
        <input
          type="number"
          name="num_questions"
          placeholder="Number of Questions"
          className="w-full p-2 border rounded"
          value={formData.num_questions}
          onChange={handleChange}
          min="1"/>
        <select
          name="difficulty"
          className="w-full p-2 border rounded"
          value={formData.difficulty}
          onChange={handleChange}>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>

        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded"
          disabled={loading}>
          {loading ? "Generating..." : "Generate MCQs"}
        </button>
      </form>

      {error && <p className="text-red-600 mt-4">{error}</p>}

      {questions.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-2">Generated MCQs:</h3>
          <ul className="space-y-4">
            {questions.map((q, idx) => (
              <li key={idx} className="border p-4 rounded">
                <p className="font-semibold">{idx + 1}. {q.question}</p>
                <ul className="ml-4 mt-2 list-disc">
                  {q.options.map((opt, i) => (
                    <li key={i}>{String.fromCharCode(65 + i)}. {opt}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
      {pdfUrl && (
    <a
    href={`http://localhost:8000${pdfUrl}`} // Use the dynamic URL from backend
    download="Exam_Paper.pdf"
    className="mt-6 inline-block text-blue-700 underline">
    Download PDF
   </a>
    )}

      </div>
      )}
       <div className="d-flex justify-content-center mt-3">
        <button
      onClick={() => navigate(-1)}
      className="bg-black text-white px-4 py-2 rounded mt-4">
      Back
      </button>
      </div>
    </div>
    </div>
  );
};

export default McqBased;
