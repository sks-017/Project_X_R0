import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'

// Simple Markdown Parser to render tables, headers, bullet points, and formatting safely.
function formatMarkdown(text) {
  if (!text) return '';
  let html = text;
  
  // Basic text styling
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  
  const lines = html.split('\n');
  let inList = false;
  let inTable = false;
  let tableRows = [];
  const formattedLines = [];
  
  for (let line of lines) {
    const trimmed = line.trim();
    
    // Check if it's a table row
    if (trimmed.startsWith('|')) {
      if (inList) {
        formattedLines.push('</ul>');
        inList = false;
      }
      if (!inTable) {
        inTable = true;
        tableRows = [];
      }
      
      // Skip table separator line (e.g. | :--- | :--- |)
      if (trimmed.includes('---') || trimmed.includes(':---')) {
        continue;
      }
      
      const cols = line.split('|').map(c => c.trim()).filter((c, i, arr) => i > 0 && i < arr.length - 1);
      tableRows.push(cols);
      continue;
    } else {
      if (inTable) {
        // Build table
        let tableHtml = '<table><thead><tr>';
        const headers = tableRows[0] || [];
        headers.forEach(h => {
          tableHtml += `<th>${h}</th>`;
        });
        tableHtml += '</tr></thead><tbody>';
        
        for (let i = 1; i < tableRows.length; i++) {
          tableHtml += '<tr>';
          tableRows[i].forEach(cell => {
            tableHtml += `<td>${cell}</td>`;
          });
          tableHtml += '</tr>';
        }
        tableHtml += '</tbody></table>';
        formattedLines.push(tableHtml);
        inTable = false;
        tableRows = [];
      }
    }

    // Headers
    if (trimmed.startsWith('### ')) {
      formattedLines.push(`<h3>${trimmed.substring(4)}</h3>`);
    } else if (trimmed.startsWith('#### ')) {
      formattedLines.push(`<h4>${trimmed.substring(5)}</h4>`);
    } else if (trimmed.startsWith('## ')) {
      formattedLines.push(`<h2>${trimmed.substring(3)}</h2>`);
    } else if (trimmed.startsWith('# ')) {
      formattedLines.push(`<h1>${trimmed.substring(2)}</h1>`);
    }
    // Bullet lists
    else if (trimmed.startsWith('- ')) {
      if (!inList) {
        formattedLines.push('<ul>');
        inList = true;
      }
      formattedLines.push(`<li>${trimmed.substring(2)}</li>`);
    }
    // Numbered lists
    else if (trimmed.match(/^\d+\.\s/)) {
      if (!inList) {
        formattedLines.push('<ol>');
        inList = true;
      }
      formattedLines.push(`<li>${trimmed.replace(/^\d+\.\s/, '')}</li>`);
    }
    // Paragraphs
    else {
      if (inList) {
        formattedLines.push('</ul>');
        inList = false;
      }
      if (trimmed) {
        formattedLines.push(`<p>${trimmed}</p>`);
      }
    }
  }
  
  if (inList) {
    formattedLines.push('</ul>');
  }
  if (inTable) {
    let tableHtml = '<table><thead><tr>';
    const headers = tableRows[0] || [];
    headers.forEach(h => {
      tableHtml += `<th>${h}</th>`;
    });
    tableHtml += '</tr></thead><tbody>';
    for (let i = 1; i < tableRows.length; i++) {
      tableHtml += '<tr>';
      tableRows[i].forEach(cell => {
        tableHtml += `<td>${cell}</td>`;
      });
      tableHtml += '</tr>';
    }
    tableHtml += '</tbody></table>';
    formattedLines.push(tableHtml);
  }
  
  return formattedLines.join('');
}

const SUGGESTIONS = [
  "What is the health of IMM-01?",
  "What is our current OEE?",
  "What are the latest anomalies?",
  "How do I fix molding flash?",
  "List active alerts",
  "List all machines"
]

export default function TechMate() {
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: `### 👋 Welcome to **TechMate AI Assistant**!\n\nI am your intelligent factory floor companion, built to help you monitor, analyze, and optimize production lines.\n\nAsk me about live machine telemetry, OEE, downtime events, or seek expert troubleshooting guides for common injection molding defects.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      context: ["System Help"]
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const handleSend = async (textToSend) => {
    const text = textToSend || inputValue.trim()
    if (!text) return

    if (!textToSend) {
      setInputValue('')
    }

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    
    // Add user message
    setMessages(prev => [...prev, {
      sender: 'user',
      text,
      timestamp
    }])

    setLoading(true)

    try {
      const res = await api.askTechMate(text)
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        context: res.context_used || []
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: `⚠️ **Error communicating with TechMate:** ${err.message || 'Unknown network error'}. Please check if the FastAPI backend is running on port 8000.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        context: []
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  return (
    <div className="page animate-in">
      <div className="page-header">
        <h1>TechMate AI</h1>
        <p>Conversational operations assistant with real-time factory database integration</p>
      </div>

      <div className="chat-layout">
        <div className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: '1.4rem' }}>🤖</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '.95rem' }}>TechMate Copilot</div>
              <div style={{ fontSize: '.72rem', color: 'var(--green)' }}>● Online | Connected to Factory DB</div>
            </div>
          </div>
          <button className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: '.78rem' }} onClick={() => setMessages(prev => [prev[0]])}>
            Clear History
          </button>
        </div>

        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}`}>
              <div className="chat-message-icon">
                {msg.sender === 'user' ? '👤' : '🤖'}
              </div>
              <div>
                <div className="chat-bubble" dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.text) }} />
                
                {msg.context && msg.context.length > 0 && (
                  <div className="chat-context-pills">
                    {msg.context.map((c, i) => (
                      <span key={i} className="chat-context-pill">🔍 Context: {c}</span>
                    ))}
                  </div>
                )}
                
                <div style={{ fontSize: '.7rem', color: 'var(--text-muted)', marginTop: 4, textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
                  {msg.timestamp}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-message assistant">
              <div className="chat-message-icon">🤖</div>
              <div className="chat-bubble" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 20px' }}>
                <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                <span style={{ color: 'var(--text-secondary)', fontSize: '.85rem' }}>TechMate is compiling factory data...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-footer">
          <div className="chat-suggest-row">
            {SUGGESTIONS.map((s, i) => (
              <button 
                key={i} 
                className="chat-suggest-chip" 
                onClick={() => handleSend(s)}
                disabled={loading}
              >
                {s}
              </button>
            ))}
          </div>

          <div className="chat-input-row">
            <input
              type="text"
              className="chat-input-field"
              placeholder="Ask TechMate about machine data, alerts, OEE, or how to troubleshoot molding defects..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button 
              className="btn btn-primary" 
              onClick={() => handleSend()}
              disabled={loading || !inputValue.trim()}
            >
              Send ⚡
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
