import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, AlertCircle, Square } from 'lucide-react';

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center">
        <Bot className="w-4 h-4 text-indigo-500" />
      </div>
      <div className="ml-3 flex items-center gap-1 px-4 py-2 bg-slate-100 rounded-2xl">
        <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
        <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
        <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot"></span>
      </div>
    </div>
  );
}

function ChatMessage({ message, isUser }) {
  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''} animate-fade-in`}>
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
        ${isUser 
          ? 'bg-gradient-to-br from-slate-700 to-slate-800' 
          : 'bg-gradient-to-br from-indigo-100 to-violet-100'
        }
      `}>
        {isUser 
          ? <User className="w-4 h-4 text-white" />
          : <Bot className="w-4 h-4 text-indigo-500" />
        }
      </div>
      
      <div className={`
        max-w-[80%] px-4 py-3 rounded-2xl
        ${isUser 
          ? 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white rounded-tr-md' 
          : 'bg-slate-100 text-slate-700 rounded-tl-md'
        }
      `}>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        {message.error && (
          <div className="flex items-center gap-1.5 mt-2 text-red-300">
            <AlertCircle className="w-3.5 h-3.5" />
            <span className="text-xs">Failed to send</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPanel({ messages, onSendMessage, isLoading, jobId, onStop }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    onSendMessage(input.trim());
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-200/60 flex flex-col h-[600px] animate-fade-in">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-indigo-500" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-800">AI Assistant</h2>
          <p className="text-xs text-slate-500">
            {jobId ? 'Ask questions about your document' : 'Upload a document to start'}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-indigo-500" />
            </div>
            <h3 className="text-lg font-semibold text-slate-700 mb-2">
              Ready to help!
            </h3>
            <p className="text-sm text-slate-500 max-w-xs">
              {jobId 
                ? "Ask me anything about your uploaded document. I'll use the content to provide accurate answers."
                : "Upload a PRD, Figma export, or screenshot to get started. I'll analyze it and answer your questions."
              }
            </p>
            
            {jobId && (
              <div className="mt-6 space-y-2">
                <p className="text-xs text-slate-400 uppercase tracking-wide font-medium">
                  Try asking:
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {[
                    "What are the main features?",
                    "Who is the target user?",
                    "What problem does this solve?"
                  ].map((suggestion, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(suggestion)}
                      className="px-3 py-1.5 text-xs text-indigo-600 bg-indigo-50 rounded-full hover:bg-indigo-100 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <ChatMessage 
                key={index} 
                message={message} 
                isUser={message.role === 'user'} 
              />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-100">
        <div className="flex items-start gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={jobId ? "Ask about your document..." : "Upload a document first..."}
              disabled={!jobId || isLoading}
              rows={1}
              className="
                w-full px-4 py-3 pr-12 rounded-xl border border-slate-200
                bg-slate-50 text-slate-700 placeholder-slate-400
                focus:outline-none
                disabled:opacity-50 disabled:cursor-not-allowed
                resize-none min-h-[48px] max-h-[120px]
                transition-all duration-200
              "
              style={{ height: 'auto' }}
              aria-label="Chat message input"
            />
          </div>
          
          {isLoading ? (
            <button
              type="button"
              onClick={onStop}
              className="
                h-[48px] w-[48px] rounded-xl flex items-center justify-center flex-shrink-0
                bg-white border border-slate-200
                hover:bg-slate-50
                text-slate-700 shadow-sm
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2
              "
              aria-label="Stop generating"
            >
              <Square className="w-4 h-4 fill-current" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() || !jobId}
              className="
                h-[48px] w-[48px] rounded-xl flex items-center justify-center flex-shrink-0
                bg-gradient-to-r from-indigo-500 to-violet-500
                hover:from-indigo-600 hover:to-violet-600
                text-white shadow-lg shadow-indigo-500/25
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
              "
              aria-label="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
