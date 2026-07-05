import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const Generate_From_Syllabus = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    filename: "",
    filetype: "pdf",
    subject: "",
    difficulty: "medium",
    course_code: "",
    qp_code: "",
  });

  const [userFiles, setUserFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [pdfUrl, setPdfUrl] = useState("");
  const [error, setError] = useState("");

  // Fetch user-specific PDFs
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/api/pdfs/", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        });
        setUserFiles(res.data.pdfs || []);
      } catch (err) {
        console.error("Failed to fetch user files:", err);
      }
    };
    fetchFiles();
  }, []);

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
      const res = await axios.post("http://127.0.0.1:8000/api/auto_generate_from_syllabus/", formData, {
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

  const renderQuestionsByMarks = (mark) =>
    questions
      .filter((q) => q.marks === mark)
      .map((q, idx) => (
        <li key={idx} className="border p-2 rounded my-2 bg-gray-100">
        <strong>{mark}-mark:</strong> {q.question_text}
        </li>
      ));

  return (
    <div className="min-h-screen bg-cover bg-center flex items-center justify-center">
      <div className="container max-w-2xl p-6 shadow-lg rounded" style={{ backgroundColor: "rgba(255, 255, 255, 0.1)", border: "1px solid #ccc" }}>
        <h2 className="text-2xl font-bold mb-4 text-center">Generate Questions from Syllabus</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <select name="filename" className="w-full p-2 border rounded" value={formData.filename} onChange={handleChange} required>
            <option value="">Select uploaded file</option>
            {userFiles.map((file, idx) => (
              <option key={idx} value={file.filename}>
                {file.filename}
              </option>
            ))}
          </select>

          <select name="filetype" className="w-full p-2 border rounded" value={formData.filetype} onChange={handleChange}>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
          </select>

          <input type="text" name="subject" placeholder="Subject" className="w-full p-2 border rounded" value={formData.subject} onChange={handleChange} required />

          <select name="difficulty" className="w-full p-2 border rounded" value={formData.difficulty} onChange={handleChange}>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>

          <input type="text" name="course_code" placeholder="Course Code" className="w-full p-2 border rounded" value={formData.course_code} onChange={handleChange} />
          <input type="text" name="qp_code" placeholder="QP Code" className="w-full p-2 border rounded" value={formData.qp_code} onChange={handleChange} />

          <button
            type="submit"
            className="bg-black text-white px-4 py-2 rounded w-full flex items-center justify-center gap-2"
            disabled={loading}>
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Generating...
              </>
            ) : (
              "Generate Questions"
            )}
          </button>
        </form>

        {error && <p className="text-red-600 mt-4 text-center">{error}</p>}

        {questions.length > 0 && (
          <div className="mt-6">
            <h3 className="text-xl font-semibold mb-2">Generated Questions:</h3>
            <ul>{renderQuestionsByMarks(2)}</ul>
            <ul>{renderQuestionsByMarks(5)}</ul>
            <ul>{renderQuestionsByMarks(10)}</ul>

            {pdfUrl && (
              <a href={`http://localhost:8000${pdfUrl}`} download="Exam_Paper.pdf" className="mt-4 inline-block text-blue-700 underline">
              Download PDF
              </a>
            )}
          </div>
        )}

        <div className="flex justify-center mt-4">
          <button onClick={() => navigate(-1)} className="bg-black text-white px-4 py-2 rounded">
          Back
          </button>
        </div>
      </div>
    </div>
  );
};

export default Generate_From_Syllabus;
