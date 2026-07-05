import React from "react";
import { Navbar, Nav, NavDropdown, Container } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import LogoutButton from "./LogoutButton";

const Dashboard = () => {
  const navigate = useNavigate();

  return (
    <>
      {/* 🔸 Navbar Section */}
      <Navbar bg="dark" variant="dark" expand="lg" sticky="top">
        <Container>
          <Navbar.Brand onClick={() => navigate("/dashboard")} style={{ cursor: "pointer" }}>
            DIGISETTER
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="navbar-content" />
          <Navbar.Collapse id="navbar-content">
            <Nav className="me-auto">
              <NavDropdown title="Upload" id="upload-dropdown">
                <NavDropdown.Item onClick={() => navigate("/upload_pdf")}>PDF</NavDropdown.Item>
                <NavDropdown.Item onClick={() => navigate("/upload_docx")}>DOCX</NavDropdown.Item>
              </NavDropdown>

              <NavDropdown title="Generate Questions" id="generate-dropdown">
                <NavDropdown.Item onClick={() => navigate("/auto_generate_from_syllabus")}>Generate_From_Syllabus</NavDropdown.Item>
                <NavDropdown.Item onClick={() => navigate("/generate-prompt")}>PromptBased</NavDropdown.Item>
                <NavDropdown.Item onClick={() => navigate("/generate_mcq_from_syllabus")}>Generate_Mcq</NavDropdown.Item>
                <NavDropdown.Item onClick={() => navigate("/generate-mcqs")}>McqBased</NavDropdown.Item>
              </NavDropdown>

              <NavDropdown title="Manage Questions" id="manage-dropdown">
                <NavDropdown.Item onClick={() => navigate("/insert")}>Insert</NavDropdown.Item>
                <NavDropdown.Item onClick={() => navigate("/questions")}>View</NavDropdown.Item>
                <NavDropdown.Item onClick={() => navigate("/delete")}>Delete</NavDropdown.Item>
              </NavDropdown>
            </Nav>

            {/* 🔸 Logout button */}
            <div className="text-danger fw-bold">
              <LogoutButton />
            </div>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      {/* 🔸 Welcome Message Block */}
      <div
        className="d-flex justify-content-center align-items-center vh-100"
        style={{
          backgroundImage: "url('/paper.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}>
        <div
          className="p-5 shadow-lg rounded text-center"
          style={{
            backgroundColor: "rgba(255, 255, 255, 0.6)",
            backdropFilter: "blur(8px)",
            border: "1px solid #ccc",
            width: "90%",
            maxWidth: "500px",
          }}>
          <h1 className="text-3xl fw-bold mb-3">Welcome to DIGISETTER</h1>
          <p className="text-lg">
            Today is{" "}
            {new Date().toLocaleDateString("en-IN", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </p>
        </div>
      </div>
    </>
  );
};

export default Dashboard;
