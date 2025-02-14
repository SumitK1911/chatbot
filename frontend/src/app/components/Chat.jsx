'use client'
import { useState } from "react";
import axios from "axios";

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const handleAsk = async () => {
    if (!question) return;
    
    const res = await axios.get(`http://127.0.0.1:8000/ask?query=${question}`);
    setAnswer(res.data.answer);
  };

  return (
    <div>
      <h2>Chatbot</h2>
      <input
        type="text"
        placeholder="Ask a question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button onClick={handleAsk}>Ask</button>

      {answer && <p>Answer: {answer}</p>}
    </div>
  );
}
