import { useState } from 'react';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!file || !jobDescription) {
      setError('Please provide both a resume PDF and a job description.');
      return;
    }

    setError('');
    setLoading(true);
    setResults(null);

    const formData = new FormData();
    formData.append('resume', file);
    formData.append('jobDescription', jobDescription);

    try {
      // Pointing to the Node.js backend
      const response = await axios.post('http://localhost:4000/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred during analysis.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto mt-12 mb-12 p-8 bg-white rounded-2xl shadow-xl border border-gray-100">
      <h1 className="text-4xl font-extrabold text-center text-gray-800 mb-8 tracking-tight">
        Smart ATS Resume Analyzer
      </h1>
      
      <form onSubmit={handleAnalyze} className="space-y-6">
        <div className="flex flex-col">
          <label className="font-semibold text-gray-700 mb-2">Upload Resume (PDF)</label>
          <input 
            type="file" 
            accept=".pdf" 
            onChange={handleFileChange} 
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 transition duration-150 cursor-pointer"
          />
        </div>

        <div className="flex flex-col">
          <label className="font-semibold text-gray-700 mb-2">Job Description</label>
          <textarea 
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            className="p-4 border border-gray-300 rounded-xl min-h-[160px] focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow text-gray-700 resize-y"
          />
        </div>

        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-lg">
            {error}
          </div>
        )}

        <button 
          type="submit" 
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 px-4 rounded-xl shadow-md transition duration-300 ease-in-out disabled:bg-gray-400 disabled:cursor-not-allowed transform hover:-translate-y-0.5 active:translate-y-0 disabled:transform-none"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing...
            </span>
          ) : 'Analyze Resume'}
        </button>
      </form>

      {results && (
        <div className="mt-10 p-8 bg-gray-50 rounded-2xl border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b pb-4">Analysis Results</h2>
          
          <div className="mb-8">
            <p className="text-gray-600 font-medium mb-1">ATS Match Score</p>
            <div className="flex items-baseline">
              <span className={`text-5xl font-extrabold ${results.ats_score >= 75 ? 'text-green-500' : results.ats_score >= 50 ? 'text-yellow-500' : 'text-red-500'}`}>
                {results.ats_score}%
              </span>
            </div>
            
            {/* Simple progress bar */}
            <div className="w-full bg-gray-200 rounded-full h-2.5 mt-4">
              <div 
                className={`h-2.5 rounded-full ${results.ats_score >= 75 ? 'bg-green-500' : results.ats_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`} 
                style={{ width: `${results.ats_score}%` }}
              ></div>
            </div>
          </div>
          
          <div className="mb-8">
            <h3 className="text-lg font-bold text-gray-800 mb-3">Recommendations:</h3>
            <ul className="space-y-2">
              {results.suggestions.map((s, index) => (
                <li key={index} className="flex items-start">
                  <span className="inline-block w-2 h-2 rounded-full bg-blue-500 mt-2 mr-3 flex-shrink-0"></span>
                  <span className="text-gray-700">{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-3">Missing Keywords to Add:</h3>
            {results.missing_keywords.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {results.missing_keywords.map((keyword, index) => (
                  <span key={index} className="px-3 py-1.5 bg-red-100 text-red-700 border border-red-200 rounded-lg text-sm font-medium shadow-sm">
                    {keyword}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-green-600 font-medium">Great job! No major keywords missing.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;