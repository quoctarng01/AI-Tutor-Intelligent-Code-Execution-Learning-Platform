/**
 * Monaco Editor wrapper for code editing in the exercise interface.
 * Provides lazy loading, fallback for SSR, and Python syntax highlighting.
 */

import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import type { EditorProps } from '@monaco-editor/react';

const MonacoEditor = lazy(() => import('@monaco-editor/react'));

/**
 * Props for the CodeEditor component.
 */
interface CodeEditorProps {
  /** Current code content */
  value: string;
  /** Callback fired when code changes */
  onChange: (value: string) => void;
  /** Whether the editor is read-only */
  readOnly?: boolean;
  /** Height of the editor container */
  height?: string;
}

/**
 * Fallback textarea component used when Monaco Editor is not yet mounted
 * or during SSR. Provides basic text editing functionality.
 */
function CodeEditorFallback({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full h-full bg-neutral-900 text-slate-200 p-4 font-mono text-sm resize-none focus:outline-none"
      placeholder="Write your Python code here..."
      spellCheck={false}
    />
  );
}

/**
 * Code editor component with Monaco Editor and textarea fallback.
 * Supports Python syntax highlighting, read-only mode, and automatic layout.
 * 
 * @param props - CodeEditorProps
 * @returns The code editor component
 */
export function CodeEditor({ value, onChange, readOnly = false, height = '100%' }: CodeEditorProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleEditorChange = useCallback(
    (val: string | undefined) => {
      if (val !== undefined) {
        onChange(val);
      }
    },
    [onChange]
  );

  const editorOptions: EditorProps['options'] = {
    minimap: { enabled: false },
    fontSize: 14,
    fontFamily: "'Fira Code', 'Cascadia Code', Consolas, monospace",
    lineNumbers: 'on',
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 4,
    insertSpaces: true,
    wordWrap: 'on',
    readOnly,
    padding: { top: 12, bottom: 12 },
    scrollbar: {
      vertical: 'auto',
      horizontal: 'auto',
      verticalScrollbarSize: 10,
      horizontalScrollbarSize: 10,
    },
  };

  if (!mounted) {
    return <CodeEditorFallback value={value} onChange={onChange} />;
  }

  return (
    <div style={{ height }}>
      <Suspense fallback={<CodeEditorFallback value={value} onChange={onChange} />}>
        <MonacoEditor
          height="100%"
          language="python"
          theme="vs-dark"
          value={value}
          onChange={handleEditorChange}
          options={editorOptions}
          loading={
            <div className="flex items-center justify-center h-full bg-neutral-900 text-slate-400">
              Loading editor...
            </div>
          }
        />
      </Suspense>
    </div>
  );
}
