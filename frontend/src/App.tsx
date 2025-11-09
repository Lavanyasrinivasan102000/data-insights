import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import Header from './components/Layout/Header';
import FileUpload from './components/Upload/FileUpload';
import ChatInterface from './components/Chat/ChatInterface';
import FileList from './components/Upload/FileList';
import { signIn } from './services/api';

const queryClient = new QueryClient();

function App() {
  const [userId, setUserId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'upload' | 'chat'>('upload');

  useEffect(() => {
    // Sign in on mount
    const initializeUser = async () => {
      try {
        const response = await signIn();
        setUserId(response.user_id);
        // Store in localStorage for persistence
        localStorage.setItem('userId', response.user_id);
      } catch (error) {
        console.error('Error signing in:', error);
      }
    };

    // Check for existing user ID
    const storedUserId = localStorage.getItem('userId');
    if (storedUserId) {
      setUserId(storedUserId);
    } else {
      initializeUser();
    }
  }, []);

  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-purple-50 to-accent-50">
        <div className="text-center animate-fade-in">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary-200 border-t-primary-600 mx-auto"></div>
            <div className="absolute inset-0 animate-pulse-slow">
              <div className="rounded-full h-16 w-16 bg-primary-400/20 mx-auto"></div>
            </div>
          </div>
          <p className="mt-6 text-lg font-semibold text-gradient">Initializing...</p>
          <p className="mt-2 text-sm text-gray-600">Setting up your workspace</p>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen">
        <Header activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="container mx-auto px-4 py-8 max-w-7xl">
          <div className="animate-fade-in-up">
            {activeTab === 'upload' ? (
              <div className="space-y-8">
                <FileUpload userId={userId} />
                <FileList userId={userId} />
              </div>
            ) : (
              <ChatInterface userId={userId} />
            )}
          </div>
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;

