import React, { useState } from 'react';
import './App.css';
import BillUploader from './components/BillUploader';
import GSTLookup from './components/GSTLookup';
import BillAnalyzer from './components/BillAnalyzer';

function App() {
  const [activeTab, setActiveTab] = useState('analyzer');
  const [analysisResult, setAnalysisResult] = useState(null);

  return (
    <div className="App">
      <header className="app-header">
        <h1>GST Bill Analyzer</h1>
        <p>Detect GST discrepancies in restaurant bills</p>
      </header>

      <nav className="tab-navigation">
        <button
          className={activeTab === 'analyzer' ? 'active' : ''}
          onClick={() => setActiveTab('analyzer')}
        >
          Bill Analyzer
        </button>
        <button
          className={activeTab === 'lookup' ? 'active' : ''}
          onClick={() => setActiveTab('lookup')}
        >
          GST Lookup
        </button>
      </nav>

      <main className="app-content">
        {activeTab === 'analyzer' && (
          <div>
            <BillUploader onAnalysisComplete={setAnalysisResult} />
            {analysisResult && <BillAnalyzer result={analysisResult} />}
          </div>
        )}

        {activeTab === 'lookup' && <GSTLookup />}
      </main>

      <footer className="app-footer">
        <p>Powered by Google Gemini AI | Built with React + Vite</p>
      </footer>
    </div>
  );
}

export default App;
