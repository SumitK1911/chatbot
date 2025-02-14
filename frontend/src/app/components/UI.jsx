'use client'
import { useState, useEffect } from "react";
import axios from "axios";
import { useSession, signIn, signOut } from "next-auth/react";
import { motion } from "framer-motion";
import { Mic, Send } from "lucide-react"; 

export default function ChatUI() {
  const { data: session } = useSession();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);

  const handleAsk = async (query) => {
    if (!query) return;
    setMessages(prevMessages => [...prevMessages, { text: query, role: 'user' }]);
    setLoading(true);
    setQuestion("");

    const res = await axios.get(`http://127.0.0.1:8000/ask?query=${query}`);
    const answer = res.data.answer;
    setMessages(prevMessages => [...prevMessages, { text: answer, role: 'ai' }]);
    setLoading(false);
  };

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQuestion(transcript);

      
      handleAsk(transcript);
    };

    recognition.start();
  };

  useEffect(() => {
    const chatContainer = document.getElementById("chat-container");
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }, [messages]);

  return (
    <div className="flex flex-col justify-center items-center h-screen p-4 bg-gray-50">
      <h1 className="text-3xl font-semibold mb-4"> Chatbot</h1>
      {!session ? (
        <button onClick={() => signIn("google")} className="px-4 py-2 bg-blue-500 text-white rounded-md">Sign in with Google</button>
      ) : (
        <div className="flex flex-col items-center">
          <p className="mb-2">Welcome, {session.user.name}</p>
          <button onClick={() => signOut()} className="px-4 py-2 bg-red-500 text-white rounded-md">Sign Out</button>
        </div>
      )}

      <div id="chat-container" className="flex flex-col w-full max-w-md mt-4 bg-white p-4 rounded-lg shadow-lg overflow-auto h-[400px]">
        {messages.map((msg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`mb-4 p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-100 self-end' : 'bg-gray-200 self-start'}`}
          >
            <p>{msg.text}</p>
          </motion.div>
        ))}
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="mb-4 p-3 rounded-lg bg-gray-200 self-start"
          >
            <p>...Loading</p>
          </motion.div>
        )}
      </div>

      <div className="mt-4 flex w-full max-w-md">
        <input
          type="text"
          placeholder="Type a message..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e)=>{
            if(e.key == "Enter"){
              e.preventDefault()
              handleAsk(question)
            }
          }}
          className="p-2 w-full border border-gray-300 rounded-l-lg"
        />
        <button
          onClick={startListening}
          className={`p-2 ${listening ? "bg-red-500" : "bg-gray-500"} text-white`}
        >
          <Mic size={20} />
        </button>
        <button
          onClick={() => handleAsk(question)}
          className="p-2 bg-blue-500 text-white rounded-r-lg"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}
