import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const PromptBased = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    subject: "",
    topic: "",
    difficulty: "medium",
    course_code: "",
    qp_code: "",
  });
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [pdfUrl, setPdfUrl] = useState("");
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setQuestions([]);
    setPdfUrl("");
    setError("");

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/generate-prompt/", formData, {
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
    <div
      className="container max-w-2xl p-6 shadow-lg rounded"
      style={{ backgroundColor: "rgba(255, 255, 255, 0.1)", border: "1px solid #ccc" }}>
      <h2 className="text-2xl font-bold mb-4 text-center">Generating Question from Prompt </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          name="subject"
          placeholder="Subject"
          required
          className="w-full p-2 border rounded"
          value={formData.subject}
          onChange={handleChange}
        />

        <input
          type="text"
          name="topic"
          placeholder="Topic"
          required
          className="w-full p-2 border rounded"
          value={formData.topic}
          onChange={handleChange}
        />

        <select
          name="difficulty"
          value={formData.difficulty}
          onChange={handleChange}
          className="w-full p-2 border rounded"
        >
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>

        <input
          type="text"
          name="course_code"
          placeholder="Course Code"
          className="w-full p-2 border rounded"
          value={formData.course_code}
          onChange={handleChange}
        />

        <input
          type="text"
          name="qp_code"
          placeholder="QP Code"
          className="w-full p-2 border rounded"
          value={formData.qp_code}
          onChange={handleChange}
        />

        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded w-full"
          disabled={loading}
        >
          {loading ? "Generating..." : "Generate Questions"}
        </button>
      </form>

      {error && <p className="text-red-500 mt-4">{error}</p>}

      {questions.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xl font-semibold mb-2">Generated Questions:</h3>
          <ul className="space-y-2 list-decimal list-inside">
            {questions.map((q, idx) => (
              <li key={idx}>
                [{q.marks}M] {q.question_text}
              </li>
            ))}
          </ul>

          {pdfUrl && (
            <a
              href={`http://localhost:8000${pdfUrl}`}
              download="Exam_Paper.pdf"
              className="mt-6 inline-block text-blue-700 underline"
            >
              Download PDF
            </a>
          )}
        </div>
      )}

      <div className="flex justify-center mt-4">
        <button
          onClick={() => navigate(-1)}
          className="bg-black text-white px-4 py-2 rounded"
        >
          Back
        </button>
      </div>
    </div>

    {/*  Loading Overlay */}
 {loading && (
  <div className="flex justify-center items-center h-screen">
    <div className="bg-white bg-opacity-90 p-6 rounded-lg shadow-md w-96 text-center border border-gray-300">
      {/* Optional icon/image */}
      <div className="flex justify-center mb-4">
        <img
          src="https://i.pinimg.com/736x/8a/b2/1b/8ab21b1edaa6d6d3405af14cd018a91b.jpg" // Replace with your actual image path
          alt="Generating"
          className="h-10 w-10"
        />
      </div>

      <h3 className="text-lg font-semibold mb-1">Generating options</h3>
      <p className="text-sm text-gray-700 mb-4">
        Please wait while we generate the questions for you. This will take around 30 seconds.
      </p>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
        <div
          className="bg-pink-500 h-full animate-pulse"
          style={{ width: "60%" }} // Or make it dynamic
        ></div>
      </div>
      <div className="text-sm text-gray-600 mt-1">60%</div>
    </div>
  </div>
)}

  </div>
);
};

export default PromptBased;
// https://i.pinimg.com/736x/8a/b2/1b/8ab21b1edaa6d6d3405af14cd018a91b.jpg