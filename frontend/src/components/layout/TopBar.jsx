import { Link, useNavigate } from "react-router-dom";

export function TopBar({ username, topic, progress }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("session_id");
    localStorage.removeItem("username");
    localStorage.removeItem("group_type");
    navigate("/login");
  };

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-slate-700 bg-slate-900">
      <div className="flex items-center gap-6">
        <Link to="/topics" className="text-sm text-blue-400 hover:text-blue-300">
          Exercises
        </Link>
        <Link to="/quiz" className="text-sm text-green-400 hover:text-green-300">
          Quiz
        </Link>
        <Link to="/surveys" className="text-sm text-purple-400 hover:text-purple-300">
          Surveys
        </Link>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-400">{username || "anonymous"}</span>
        <button
          onClick={handleLogout}
          className="text-sm text-slate-400 hover:text-slate-300"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
