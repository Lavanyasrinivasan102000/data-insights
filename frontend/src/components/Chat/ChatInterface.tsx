import React, { useState, useRef, useEffect } from 'react';
import { sendMessage, ChatMessageResponse } from '../../services/api';
import MessageBubble from './MessageBubble';
import ToolCallDisplay from './ToolCallDisplay';
import BarChart from '../Visualization/BarChart';
import LineChart from '../Visualization/LineChart';
import KPICard from '../Visualization/KPICard';
import DataTable from '../Visualization/DataTable';
import InsightsPanel from '../Visualization/InsightsPanel';

interface ChatInterfaceProps {
  userId: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  data?: ChatMessageResponse['data'];
  visualization?: ChatMessageResponse['visualization'];
  toolCalls?: {
    sql_query?: string;
    file_id?: string;
    row_count?: number;
  };
  timestamp: Date;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ userId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendMessage({
        user_id: userId,
        message: input,
        session_id: sessionId || undefined,
      });

      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      // Extract tool call information from response
      const toolCalls = response.data?.sql_query ? {
        sql_query: response.data.sql_query,
        file_id: response.data.file_id,
        row_count: response.data.rows?.length || 0,
      } : undefined;

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        data: response.data,
        visualization: response.visualization,
        toolCalls,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="card flex flex-col h-[calc(100vh-200px)] overflow-hidden animate-fade-in-up">
      <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-primary-50/50 to-accent-50/50">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-display font-bold text-gray-900">Chat with Your Data</h2>
            <p className="text-sm text-gray-600 mt-0.5">
              Ask questions about your uploaded data
            </p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin bg-gradient-to-b from-white to-gray-50/50">
        {messages.length === 0 ? (
          <div className="text-center py-16 animate-fade-in">
            <div className="w-24 h-24 mx-auto rounded-3xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center mb-6 shadow-lg">
              <svg className="w-12 h-12 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-xl font-bold text-gray-900 mb-2">Start a conversation</p>
            <p className="text-gray-500 mb-6">Ask questions about your data</p>
            <div className="inline-flex flex-col space-y-2">
              <div className="px-4 py-2 bg-white rounded-xl border border-gray-200 shadow-sm text-sm text-gray-600">
                💡 Try asking: "What are the total sales?"
              </div>
              <div className="px-4 py-2 bg-white rounded-xl border border-gray-200 shadow-sm text-sm text-gray-600">
                📊 "Show me a chart of sources"
              </div>
              <div className="px-4 py-2 bg-white rounded-xl border border-gray-200 shadow-sm text-sm text-gray-600">
                🔍 "List all deal stages"
              </div>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className="animate-fade-in-up" style={{ animationDelay: `${index * 50}ms` }}>
              {/* Only show MessageBubble if it's not an insights visualization */}
              {message.visualization?.type !== 'insights' && (
                <MessageBubble message={message} />
              )}

              {/* Show tool calls */}
              {message.toolCalls && (
                <ToolCallDisplay
                  sqlQuery={message.toolCalls.sql_query}
                  fileId={message.toolCalls.file_id}
                  rowCount={message.toolCalls.row_count}
                />
              )}

              {/* Show visualizations */}
              {message.visualization && (
                <div className={message.visualization.type === 'insights' ? 'mt-4' : 'mt-4 ml-14'}>
                  {message.visualization.type === 'bar_chart' &&
                    message.visualization.input_data && (
                      <BarChart data={message.visualization.input_data} />
                    )}
                  {message.visualization.type === 'line_chart' &&
                    message.visualization.input_data && (
                      <LineChart data={message.visualization.input_data} />
                    )}
                  {message.visualization.type === 'kpi' &&
                    message.visualization.input_data && (
                      <KPICard data={message.visualization.input_data[0]} />
                    )}
                  {message.visualization.type === 'insights' && (
                      <InsightsPanel insightsText={message.content} />
                    )}
                  {message.visualization.type === 'table' &&
                    message.data?.rows && (
                      <DataTable
                        rows={message.data.rows}
                        columns={message.data.columns || []}
                      />
                    )}
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="flex items-center space-x-3 p-4 bg-gradient-to-r from-primary-50 to-accent-50 rounded-xl border border-primary-200 animate-fade-in">
            <div className="relative">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-primary-200 border-t-primary-600"></div>
              <div className="absolute inset-0 animate-ping rounded-full h-5 w-5 border-2 border-primary-400 opacity-20"></div>
            </div>
            <span className="text-sm font-semibold text-primary-700">Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-6 border-t border-gray-200 bg-white">
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your data..."
              className="input-premium w-full pr-12"
              disabled={loading}
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="btn-primary flex items-center space-x-2"
          >
            <span>Send</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
