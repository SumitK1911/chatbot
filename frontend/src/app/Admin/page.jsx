'use client'
import { useSession, signIn, signOut } from "next-auth/react";
import { useState } from "react";
import axios from "axios";

export default function Admin() {
  const { data: session } = useSession();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const addFAQ = async () => {
    if (!question || !answer) return;
    try {
      await axios.post("http://127.0.0.1:8000/add_faq", { question, answer });
      alert("FAQ added successfully!");
      setQuestion("");
      setAnswer("");
    } catch (error) {
      console.error(error);
      alert("Failed to add FAQ.");
    }
  };

  if (!session) {
    return <button onClick={() => signIn("google")}>Sign in with Google</button>;
  }

  return (
    <div style={{ textAlign: "center", padding: "20px" }}>
      <h1>Admin Panel</h1>
      <p>Welcome, {session.user.name}</p>
      <button onClick={() => signOut()}>Sign Out</button>

      <h3>Add FAQ</h3>
      <input
        type="text"
        placeholder="Question"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <input
        type="text"
        placeholder="Answer"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
      />
      <button onClick={addFAQ}>Add FAQ</button>
    </div>
  );
}
