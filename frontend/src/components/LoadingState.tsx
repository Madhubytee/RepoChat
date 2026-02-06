"use client";

import { useEffect, useState } from "react";

interface LoadingStateProps {
  status: string;
}

const STEPS = [
  { key: "cloning", label: "Cloning repository" },
  { key: "processing", label: "Processing code files" },
  { key: "embedding", label: "Creating embeddings" },
  { key: "ready", label: "Ready to chat" },
];

export default function LoadingState({ status }: LoadingStateProps) {
  const [dots, setDots] = useState("");

  useEffect(() => {
    if (status === "ready") return;
    const interval = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."));
    }, 500);
    return () => clearInterval(interval);
  }, [status]);

  const currentIndex = STEPS.findIndex((s) => s.key === status);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <div className="w-full max-w-md space-y-4">
        <h2 className="text-xl font-semibold text-white text-center mb-6">
          Setting up your repo
        </h2>

        {STEPS.map((step, i) => {
          const isDone = i < currentIndex || status === "ready";
          const isCurrent = step.key === status && status !== "ready";

          return (
            <div key={step.key} className="flex items-center gap-3">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-sm
                  ${isDone ? "bg-green-500 text-white" : ""}
                  ${isCurrent ? "bg-blue-500 text-white animate-pulse" : ""}
                  ${!isDone && !isCurrent ? "bg-gray-700 text-gray-500" : ""}
                `}
              >
                {isDone ? "\u2713" : i + 1}
              </div>
              <span
                className={`${isDone ? "text-green-400" : ""} ${isCurrent ? "text-white" : ""} ${!isDone && !isCurrent ? "text-gray-600" : ""}`}
              >
                {step.label}
                {isCurrent ? dots : ""}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
