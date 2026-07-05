import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';


const UploadDOCX = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
   const [fileTypeTag, setFileTypeTag] = useState("syllabus");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

 
  const handleUpload = async (event) => {
    event.preventDefault(); // Prevent form from refreshing the page

    const token = localStorage.getItem('access_token'); // Make sure this matches your login storage
    if (!token) {
      console.error("Token is missing");
      alert("Please log in to upload.");
      return;
    }

    if (!file) {
      alert("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/api/upload-docx/',
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      console.log('Upload success:', response.data);
      alert('Upload successful!');
    } catch (error) {
      console.error('Upload failed:', error.response?.data || error.message);
      alert('Upload failed!');
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center vh-100" style={{ backgroundImage: "url('/your-bg.jpg')", backgroundSize: "cover" }}>
      <div className="card p-5 shadow-lg" style={{ backgroundColor: "rgba(255, 255, 255, 0.0)", border: "1px solid #ccc", width: "400px" }}>
        <h2 className="text-center mb-4">Upload Word DOCX</h2>

        <div className="text-center mb-3">
          <a href="/example_syllabus.docx" target="_blank" rel="noopener noreferrer" className="text-primary">
          View Example Syllabus Format
          </a>
        </div>

        <div className="alert alert-warning text-sm mb-3" role="alert">
        Please upload only syllabus files that contain unit-wise topics. Avoid including course outcomes, instructions, cover pages, or department headers.
        </div>

        <form onSubmit={handleUpload}>
          <div className="mb-3">
            <input
              type="file"
              className="form-control"
              accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={handleFileChange}/>
          </div>

          <div className="mb-3">
            <select
              className="form-control"
              value={fileTypeTag}
              onChange={(e) => setFileTypeTag(e.target.value)}>
              <option value="syllabus">Syllabus</option>
              <option value="notes">Notes</option>
            </select>
          </div>

          <button type="submit" className="btn btn-dark w-100">Upload DOCX</button>

          <div className="d-flex justify-content-center mt-3">
            <button onClick={() => navigate(-1)} className="btn btn-dark px-4 py-2 rounded mt-4">
            Back
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UploadDOCX;
