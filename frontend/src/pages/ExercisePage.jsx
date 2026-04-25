import { useState } from "react";
import { useParams } from "react-router-dom";

import { CodeEditor } from "../components/exercise/CodeEditor";
import { ProblemPane } from "../components/exercise/ProblemPane";
import { ResultBadge } from "../components/exercise/ResultBadge";
import { SubmitButton } from "../components/exercise/SubmitButton";
import { TopBar } from "../components/layout/TopBar";
import { HintPanel } from "../components/hints/HintPanel";
import { useExercise } from "../hooks/useExercise";
import { useHintSystem } from "../hooks/useHintSystem";
import { useSubmit } from "../hooks/useSubmit";

export default function ExercisePage() {
  const { exerciseId } = useParams();
  const sessionId = localStorage.getItem("session_id");
  const username = localStorage.getItem("username");
  const { exercise, loading, elapsedSeconds } = useExercise(exerciseId);
  const hintSystem = useHintSystem(sessionId, exerciseId);
  const { submit, result, code, setCode, isSubmitting } = useSubmit(sessionId, exerciseId);

  if (loading) {
    return (
      <div style={{ 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "center", 
        height: "100vh",
        backgroundColor: "#020617",
        color: "#e2e8f0"
      }}>
        Loading...
      </div>
    );
  }

  return (
    <div style={{ 
      display: "flex", 
      flexDirection: "column", 
      height: "100vh",
      backgroundColor: "#020617",
      color: "#e2e8f0"
    }}>
      {/* Top Bar */}
      <header style={{ 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "space-between",
        padding: "12px 16px",
        borderBottom: "1px solid #334155",
        backgroundColor: "#0f172a",
        flexShrink: 0
      }}>
        <div style={{ fontSize: "14px", color: "#cbd5e1" }}>
          User: {username || "anonymous"}
        </div>
        <div style={{ fontSize: "14px", color: "#94a3b8" }}>
          Topic: {exercise?.topic || "N/A"}
        </div>
        <div style={{ fontSize: "14px", color: "#cbd5e1" }}>
          {result?.is_correct ? 1 : 0} / 1 complete
        </div>
      </header>
      
      {/* Main Content */}
      <div style={{ 
        display: "flex", 
        flex: 1,
        minHeight: 0
      }}>
        
        {/* Left Panel - Problem + Code Editor (65%) */}
        <div style={{ 
          display: "flex", 
          flexDirection: "column",
          width: "65%",
          borderRight: "1px solid #334155"
        }}>
          
          {/* Problem Pane - fixed height */}
          <div style={{ 
            height: "180px",
            flexShrink: 0,
            overflow: "hidden",
            borderBottom: "1px solid #334155"
          }}>
            <ProblemPane exercise={exercise} />
          </div>
          
          {/* Code Editor - takes remaining space */}
          <div style={{ 
            flex: 1,
            minHeight: 0,
            backgroundColor: "#1e1e1e"
          }}>
            <CodeEditor value={code} onChange={setCode} />
          </div>
          
          {/* Submit Bar */}
          <div style={{ 
            height: "56px",
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "0 12px",
            borderTop: "1px solid #334155",
            backgroundColor: "#0f172a"
          }}>
            <SubmitButton
              loading={isSubmitting}
              onClick={() => submit(code, hintSystem.currentLevel, elapsedSeconds)}
            />
            <ResultBadge result={result} />
          </div>
        </div>
        
        {/* Right Panel - Hints (35%) */}
        <div style={{ 
          width: "35%",
          display: "flex",
          flexDirection: "column",
          minHeight: 0
        }}>
          <HintPanel
            hints={hintSystem.hints}
            currentLevel={hintSystem.currentLevel}
            isExhausted={hintSystem.isExhausted}
            isLoading={hintSystem.isLoading}
            onRequestHint={hintSystem.requestHint}
            isSolved={result?.is_correct}
          />
        </div>
      </div>
    </div>
  );
}
