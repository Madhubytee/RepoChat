"use client";

import { useState } from "react";

interface RepoInputProps {
  onSubmit: (url: string) => void;
  isProcessing: boolean;
}

export default function RepoInput({ onSubmit, isProcessing }: RepoInputProps) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");

  const normalizeGitHubUrl = (input: string): string => {
    const trimmed = input.trim();

    if (trimmed.startsWith("https://github.com/")) {
      return trimmed;
    }

    //makes sure its in owner/repo format
    const ownerRepoPattern = /^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/;
    if (ownerRepoPattern.test(trimmed)) {
      return `https://github.com/${trimmed}`;
    }

    return trimmed;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!url.trim()) {
      setError("Please enter a repository");
      return;
    }

    const normalizedUrl = normalizeGitHubUrl(url);

    if (!normalizedUrl.startsWith("https://github.com/")) {
      setError("Enter a GitHub URL or owner/repo format (e.g., facebook/react)");
      return;
    }

    onSubmit(normalizedUrl);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-2xl">
        <h1 className="text-4xl font-bold text-center mb-2 text-white">
          RepoChat
        </h1>
        <p className="text-center text-gray-400 mb-8">
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="owner/repo or https://github.com/owner/repo"
              disabled={isProcessing}
              className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg
                text-white placeholder-gray-500 focus:outline-none focus:ring-2
                focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isProcessing}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium
                hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500
                disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isProcessing ? "Processing..." : "Process Repo"}
            </button>
          </div>

          {error && (
            <p className="text-red-400 text-sm text-center">{error}</p>
          )}
        </form>

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Paste a public GitHub repository URL or use owner/repo format.</p>
        </div>
      </div>
    </div>
  );
}
