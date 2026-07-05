import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './components/Home';
import Login from './components/Login';
import Signup from './components/Signup';
import Dashboard from './components/Dashboard'; 
import UploadPDF from './components/UploadPDF';
import UploadDOCX from './components/UploadDOCX';
import InsertQuestion from './components/InsertQuestion';
import QuestionView from './components/QuestionView';
import EditQuestion from './components/EditQuestion';
import PromptBased from './components/PromptBased';
import McqBased from './components/McqBased';
import Generate_From_Syllabus from './components/Generate_From_Syllabus';
import GenerateMcq from './components/GenerateMcq';


function App() {
  const isUserAuthenticated = !!localStorage.getItem('access_token');
  // const isAuthenticated = !!localStorage.getItem("access_token");


  return (
    <Router>
      <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={isUserAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
        {/* UPLOADING */}
        <Route path="/upload_pdf" element={isUserAuthenticated ? <UploadPDF /> : <Navigate to="/login" />} />
        <Route path="/upload_docx" element={isUserAuthenticated ? <UploadDOCX /> : <Navigate to="/login" />} />
        {/* MANAGE QUESTIONS */}
        <Route path="/insert" element={isUserAuthenticated ? <InsertQuestion /> : <Navigate to="/login" />} />
        <Route path="/questions" element={<QuestionView />} />
        <Route path="/delete" element={<EditQuestion />} />
        {/* DASHBOARD */}
        <Route path="/auto_generate_from_syllabus" element={<Generate_From_Syllabus/>} />
        <Route path="/generate-prompt" element={<PromptBased/>} />
        <Route path="/generate_mcq_from_syllabus" element={<GenerateMcq/>} />
        <Route path="/generate-mcqs" element={<McqBased />} />
       
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;
