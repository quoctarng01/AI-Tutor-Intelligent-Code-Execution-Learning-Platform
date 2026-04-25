import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [groupType, setGroupType] = useState("tutor");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleStart = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post("/session/start", { username, group_type: groupType });
      localStorage.setItem("session_id", data.id);
      localStorage.setItem("username", data.username);
      localStorage.setItem("group_type", data.group_type ?? groupType);
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token);
      }
      navigate("/topics");
    } catch (_err) {
      setError("Unable to start session.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
      <div className="w-full max-w-md bg-slate-900 p-6 rounded-lg border border-slate-800">
        <h1 className="text-xl font-semibold">AI Tutor Login</h1>
        <input
          className="mt-4 w-full px-3 py-2 rounded bg-slate-800 border border-slate-700"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <select
          className="mt-3 w-full px-3 py-2 rounded bg-slate-800 border border-slate-700"
          value={groupType}
          onChange={(e) => setGroupType(e.target.value)}
        >
          <option value="tutor">tutor</option>
          <option value="control">control</option>
        </select>
        <button
          onClick={handleStart}
          disabled={loading}
          className="mt-4 w-full py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700"
        >
          {loading ? "Starting..." : "Start Session"}
        </button>
        {error ? <p className="mt-3 text-sm text-red-400">{error}</p> : null}
      </div>
    </div>
  );
}
