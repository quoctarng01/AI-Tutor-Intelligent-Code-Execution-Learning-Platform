import { useState, useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";

export function CodeEditor({ value, onChange }) {
  const [isLoading, setIsLoading] = useState(true);
  const [editorReady, setEditorReady] = useState(false);
  const [useFallback, setUseFallback] = useState(false);
  const containerRef = useRef(null);

  // Fallback timeout - if Monaco doesn't load in 5 seconds, use textarea
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (!editorReady) {
        console.log("[CodeEditor] Monaco timed out, using fallback textarea");
        setUseFallback(true);
      }
    }, 5000);
    return () => clearTimeout(timeout);
  }, [editorReady]);

  function handleEditorDidMount(editor, monaco) {
    console.log("[CodeEditor] Monaco mounted successfully!");
    setEditorReady(true);
    setIsLoading(false);
  }

  // Fallback textarea for when Monaco fails
  if (useFallback) {
    return (
      <div style={{ 
        height: "100%", 
        width: "100%",
        backgroundColor: "#1e1e1e",
        padding: "10px"
      }}>
        <textarea
          style={{
            width: "100%",
            height: "100%",
            backgroundColor: "#1e1e1e",
            color: "#d4d4d4",
            border: "none",
            outline: "none",
            fontFamily: "Consolas, 'Courier New', monospace",
            fontSize: "14px",
            lineHeight: "1.5",
            resize: "none",
            padding: "0"
          }}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="// Write your Python code here..."
          spellCheck={false}
        />
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      style={{ 
        height: "100%", 
        width: "100%",
        backgroundColor: "#1e1e1e",
        position: "relative"
      }}
    >
      {/* Debug header */}
      <div style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        padding: "4px 8px",
        backgroundColor: "#2d2d2d",
        borderBottom: "1px solid #404040",
        fontSize: "11px",
        color: editorReady ? "#4ade80" : "#fbbf24",
        zIndex: 10,
        display: "flex",
        alignItems: "center",
        gap: "8px"
      }}>
        <span style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          backgroundColor: editorReady ? "#4ade80" : "#fbbf24"
        }} />
        <span>Code Editor ({editorReady ? "Monaco Active" : "Loading..."})</span>
      </div>
      
      {/* Monaco Editor Container */}
      <div style={{ 
        position: "absolute",
        top: "24px",
        left: 0,
        right: 0,
        bottom: 0
      }}>
        <Editor
          height="100%"
          width="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={value}
          onChange={(val) => onChange(val || "")}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: "Consolas, 'Courier New', monospace",
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            wordWrap: "off",
            padding: { top: 10, bottom: 10 },
            renderLineHighlight: "all",
            cursorStyle: "line",
            cursorBlinking: "blink",
            scrollbar: {
              vertical: "visible",
              horizontal: "visible",
              verticalScrollbarSize: 14,
              horizontalScrollbarSize: 14,
            },
          }}
          loading={
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center", 
              height: "100%", 
              color: "#94a3b8",
              backgroundColor: "#1e1e1e",
              fontSize: "14px"
            }}>
              Loading Monaco Editor...
            </div>
          }
        />
      </div>
    </div>
  );
}
