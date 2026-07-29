'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, TrendingUp, AlertTriangle, MessageSquare } from 'lucide-react';

interface Signal {
  id: string;
  timestamp: string;
  multiplier: number;
  confidence: number;
  color: string;
  band: string;
}

export default function Dashboard() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [connected, setConnected] = useState(false);
  const [marketStatus, setMarketStatus] = useState('cold');

  useEffect(() => {
    // Simulate WebSocket connection
    const ws = new WebSocket('ws://localhost:8765');
    
    ws.onopen = () => {
      setConnected(true);
      console.log('Connected to WebSocket');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'signal') {
        setSignals(prev => [data.payload, ...prev].slice(0, 50));
        
        // Update market status based on confidence
        if (data.payload.confidence > 0.7) {
          setMarketStatus('hot');
        } else if (data.payload.confidence > 0.4) {
          setMarketStatus('warm');
        } else {
          setMarketStatus('cold');
        }
      }
    };

    ws.onclose = () => setConnected(false);

    return () => ws.close();
  }, []);

  const chartData = signals.map(s => ({
    time: new Date(s.timestamp).toLocaleTimeString(),
    multiplier: s.multiplier,
    confidence: s.confidence * 100,
  })).reverse();

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-2">MomentoCore Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
            connected ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
          }`}>
            <Activity size={16} />
            <span>{connected ? 'Live' : 'Disconnected'}</span>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
            marketStatus === 'hot' ? 'bg-pink-900 text-pink-300' :
            marketStatus === 'warm' ? 'bg-purple-900 text-purple-300' :
            'bg-blue-900 text-blue-300'
          }`}>
            <TrendingUp size={16} />
            <span>Market: {marketStatus.toUpperCase()}</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          title="Total Signals" 
          value={signals.length.toString()} 
          icon={<Activity />} 
        />
        <StatCard 
          title="Avg Confidence" 
          value={signals.length > 0 
            ? `${(signals.reduce((acc, s) => acc + s.confidence, 0) / signals.length * 100).toFixed(1)}%` 
            : '0%'} 
          icon={<TrendingUp />} 
        />
        <StatCard 
          title="High Value (>10x)" 
          value={signals.filter(s => s.multiplier >= 10).length.toString()} 
          icon={<AlertTriangle />} 
        />
        <StatCard 
          title="Agent Chat" 
          value="Online" 
          icon={<MessageSquare />} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-gray-900 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Multiplier Trends</h2>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="time" stroke="#666" />
              <YAxis stroke="#666" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
              />
              <Line type="monotone" dataKey="multiplier" stroke="#ff6b6b" strokeWidth={2} />
              <Line type="monotone" dataKey="confidence" stroke="#4ecdc4" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Signals</h2>
          <div className="space-y-3">
            {signals.slice(0, 10).map(signal => (
              <SignalCard key={signal.id} signal={signal} />
            ))}
            {signals.length === 0 && (
              <p className="text-gray-500 text-center py-8">Waiting for signals...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon }: { title: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-gray-900 rounded-lg p-6 flex items-center justify-between">
      <div>
        <p className="text-gray-400 text-sm mb-1">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
      <div className="text-gray-500">{icon}</div>
    </div>
  );
}

function SignalCard({ signal }: { signal: Signal }) {
  const colorClass = 
    signal.color === 'pink' ? 'bg-pink-900/50 border-pink-700' :
    signal.color === 'purple' ? 'bg-purple-900/50 border-purple-700' :
    'bg-blue-900/50 border-blue-700';

  return (
    <div className={`p-4 rounded-lg border ${colorClass}`}>
      <div className="flex justify-between items-center mb-2">
        <span className="font-mono text-lg">{signal.multiplier.toFixed(2)}x</span>
        <span className="text-xs text-gray-400">
          {new Date(signal.timestamp).toLocaleTimeString()}
        </span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="capitalize">{signal.band}</span>
        <span className={`${signal.confidence > 0.7 ? 'text-green-400' : 'text-yellow-400'}`}>
          {(signal.confidence * 100).toFixed(0)}% conf
        </span>
      </div>
    </div>
  );
}
