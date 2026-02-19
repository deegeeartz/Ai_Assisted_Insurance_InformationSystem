
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Upload, FileText } from 'lucide-react';
import { fetchManuals, uploadManual } from '../../services/api';

export function ProductManager() {
  const { token } = useAuth();
  const [manuals, setManuals] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [productType, setProductType] = useState('life_basic');

  useEffect(() => {
    if (token) loadManuals();
  }, [token]);

  const loadManuals = async () => {
    try {
        const data = await fetchManuals(token!); // token check handled in useEffect
        setManuals(data);
    } catch (e) {
        console.error(e);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !token) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('product_type', productType);
      formData.append('version', 'v' + new Date().getFullYear());

      await uploadManual(token, formData);
      alert('Manual uploaded successfully!');
      setFile(null);
      loadManuals();
    } catch (err) {
      console.error(err);
      alert('Error uploading file.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Upload Section */}
      <div className="card p-6 border-2 border-dashed border-slate-300 hover:border-blue-500 transition-colors">
        <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center">
            <Upload className="w-5 h-5 mr-2" /> Upload New Underwriting Manual
        </h3>
        <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Product Type</label>
                    <select 
                        className="w-full p-2 border rounded-lg"
                        value={productType}
                        onChange={e => setProductType(e.target.value)}
                    >
                        <option value="life_basic">Life Protection</option>
                        <option value="auto_comprehensive">Auto Insurance</option>
                        <option value="gadget_protection">Gadget Protection</option>
                        <option value="new_product">New Product (Custom)</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">PDF Rules File</label>
                    <input 
                        type="file" 
                        accept=".pdf"
                        onChange={e => setFile(e.target.files?.[0] || null)}
                        className="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                </div>
            </div>
            
            <div className="flex justify-end">
                <button 
                    type="submit" 
                    disabled={!file || uploading}
                    className="btn btn-primary"
                >
                    {uploading ? 'Ingesting...' : 'Upload & Ingest'}
                </button>
            </div>
        </form>
      </div>

      {/* List Section */}
      <div className="card">
        <div className="p-4 border-b border-slate-200">
            <h3 className="font-bold text-slate-900">Active Manuals</h3>
        </div>
        <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
                <tr>
                    <th className="px-6 py-3">Filename</th>
                    <th className="px-6 py-3">Product</th>
                    <th className="px-6 py-3">Version</th>
                    <th className="px-6 py-3">Status</th>
                </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
                {manuals.map((m: any) => (
                    <tr key={m.id}>
                        <td className="px-6 py-3 flex items-center">
                            <FileText className="w-4 h-4 mr-2 text-slate-400" /> {m.filename}
                        </td>
                        <td className="px-6 py-3">{m.product_type}</td>
                        <td className="px-6 py-3 font-mono text-xs">{m.version}</td>
                        <td className="px-6 py-3">
                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Active</span>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
      </div>
    </div>
  );
}
