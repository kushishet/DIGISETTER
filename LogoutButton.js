import { useNavigate } from "react-router-dom";

const LogoutButton = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Clear tokens or user data
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    // Redirect to login page
    navigate("/login");
  };

  return (
    <button
      onClick={handleLogout}
      className="text-danger fw-bold">
      Logout
    </button>
  );
};

export default LogoutButton;