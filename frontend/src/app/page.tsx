"use client";

import { useState } from "react";
import axios from "axios";
import RepoInput from "@/components/RepoInput";
import ChatInterface from "@/components/ChatInterface";
import LoadingState from "@/components/LoadingState";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isReady, setIsReady] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");

  const handleProcessRepo = async (url: string) => {
    setRepoUrl(url);
    setIsProcessing(true);
    setError("");
    setProcessingStatus("cloning");

    try {
      const res = await axios.post(`${API_URL}/api/process-repo`, {
        github_url: url,
      });

      const sid = res.data.session_id;
      setSessionId(sid);
      setIsProcessing(false);
      setIsReady(true);
      setProcessingStatus("ready");
    } catch (err: unknown) {
      setIsProcessing(false);
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Failed to process repository. Please try again.");
      }
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!sessionId) return;

    const userMsg: Message = { role: "user", content: message };
    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message }),
      });

      if (!res.ok) {
        throw new Error("Chat request failed");
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let fullText = "";

      //Add placeholder assistant message
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "" },
      ]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;

        //Parse out sources if present
        const sourceMarker = "\n\n---SOURCES---\n";
        let displayText = fullText;
        let sources: string[] = [];

        if (fullText.includes(sourceMarker)) {
          const parts = fullText.split(sourceMarker);
          displayText = parts[0];
          sources = parts[1]
            .split("\n")
            .filter((s) => s.trim().length > 0);
        }

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: displayText,
            sources,
          };
          return updated;
        });
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  //Error display
  if (error && !isProcessing && !isReady) {
    return (
      <div className="min-h-screen bg-gray-900 p-4">
        <RepoInput onSubmit={handleProcessRepo} isProcessing={false} />
        <div className="text-center mt-4">
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-4">
      {!isProcessing && !isReady && (
        <RepoInput onSubmit={handleProcessRepo} isProcessing={isProcessing} />
      )}

      {isProcessing && <LoadingState status={processingStatus} />}

      {isReady && sessionId && (
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isSending}
          repoUrl={repoUrl}
        />
      )}
    </div>
  );
}
