import { useState, useCallback } from 'react';
import axios from 'axios';
import Header from './components/Header';
import SummaryBox from './components/SummaryBox';
import UploadCard from './components/UploadCard';
import ChatPanel from './components/ChatPanel';
import ErrorBoundary from './components/ErrorBoundary';
import ToastContainer from './components/ToastContainer';
import useToast from './hooks/useToast';

const API_BASE_URL = 'http://localhost:8000';

function AppContent() {
  // Toast notifications
  const { toasts, addToast, removeToast } = useToast();
  
  // Upload state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Job state
  const [jobId, setJobId] = useState(null);
  // eslint-disable-next-line no-unused-vars
  const [jobStatus, setJobStatus] = useState(null);
  
  // Summary state
  const [summary, setSummary] = useState(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Poll for job status
  const pollJobStatus = useCallback(async (id) => {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;
    
    const poll = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/job/${id}/status`);
        const status = response.data.status;
        setJobStatus(status);
        
        if (status === 'completed') {
          // Fetch summary
          const summaryResponse = await axios.get(`${API_BASE_URL}/summary/${id}`);
          setSummary(summaryResponse.data);
          setIsSummaryLoading(false);
          addToast('Document processed successfully!', 'success');
          return;
        } else if (status === 'failed') {
          setIsSummaryLoading(false);
          const errorMsg = response.data.error || 'Processing failed';
          addToast(errorMsg, 'error');
          console.error('Job failed:', response.data.error);
          return;
        }
        
        // Continue polling
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else {
          setIsSummaryLoading(false);
          addToast('Processing timed out. Please try again.', 'error');
          console.error('Job timed out');
        }
      } catch (error) {
        console.error('Error polling job status:', error);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setIsSummaryLoading(false);
          addToast('Failed to check processing status', 'error');
        }
      }
    };
    
    poll();
  }, [addToast]);

  // Handle file upload
  const handleUpload = useCallback(async (files) => {
    setIsUploading(true);
    setUploadProgress(0);
    setSummary(null);
    setMessages([]);
    
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        },
      });
      
      const { job_id } = response.data;
      setJobId(job_id);
      setIsSummaryLoading(true);
      addToast('Files uploaded! Processing started...', 'info');
      
      // Start polling for job status
      pollJobStatus(job_id);
      
    } catch (error) {
      console.error('Upload failed:', error);
      const errorMsg = error.response?.data?.detail || 'Upload failed. Please try again.';
      addToast(errorMsg, 'error');
      throw error;
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [pollJobStatus, addToast]);

  // Handle chat message
  const handleSendMessage = useCallback(async (content) => {
    if (!jobId) return;
    
    // Add user message
    const userMessage = { role: 'user', content };
    setMessages(prev => [...prev, userMessage]);
    setIsChatLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: content,
        job_id: jobId,
      });
      
      // Add AI response
      const aiMessage = { role: 'assistant', content: response.data.response };
      setMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error('Chat failed:', error);
      // Add error message
      const errorMessage = { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.',
        error: true 
      };
      setMessages(prev => [...prev, errorMessage]);
      addToast('Failed to get response', 'error');
    } finally {
      setIsChatLoading(false);
    }
  }, [jobId, addToast]);

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Section */}
        <section className="mb-8">
          <SummaryBox 
            summary={summary} 
            isLoading={isSummaryLoading}
            jobId={jobId}
          />
        </section>
        
        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Card */}
          <section>
            <UploadCard 
              onUpload={handleUpload}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
            />
          </section>
          
          {/* Chat Panel */}
          <section>
            <ChatPanel 
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isChatLoading}
              jobId={jobId}
            />
          </section>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="py-6 text-center text-sm text-slate-400">
        <p>Know Your Product &copy; {new Date().getFullYear()} — AI-Powered Documentation Analysis</p>
      </footer>
      
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
