import { InsurDrop } from './InsurDrop';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
      <div className="text-center p-8">
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">Partner Website Demo</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-8">
          The floating widget below is what partners embed on their sites.
        </p>
        <div className="p-6 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 max-w-md mx-auto">
          <p className="text-sm text-slate-500">
            "We are proud to partner with Heirs Insurance to bring you instant protection."
          </p>
        </div>
      </div>
      
      {/* The Actual Widget */}
      <InsurDrop />
    </div>
  );
}

export default App;
