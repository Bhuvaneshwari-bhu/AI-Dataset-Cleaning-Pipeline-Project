import { useState } from 'react';
import { analyzeDataset } from '../services/api';

export function useAnalysis() {
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async (uploadId, options = {}) => {
    setAnalyzing(true);
    setError(null);
    try {
      const response = await analyzeDataset(uploadId, options);
      return response.data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setAnalyzing(false);
    }
  };

  return { analyze, analyzing, error };
}
