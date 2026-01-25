import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const FILE_ICONS = {
  'application/pdf': FileText,
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileText,
  'text/markdown': FileText,
  'text/plain': FileText,
  'image/png': Image,
  'image/jpeg': Image,
  'image/jpg': Image,
};

const ACCEPTED_FILES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/markdown': ['.md'],
  'text/plain': ['.txt'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
};

export default function UploadCard({ onUpload, isUploading, uploadProgress }) {
  const [files, setFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState({}); // 'pending' | 'uploading' | 'success' | 'error'

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: `${file.name}-${Date.now()}`,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
    }));
    setFiles(prev => [...prev, ...newFiles]);
    
    // Initialize status for new files
    const newStatus = {};
    newFiles.forEach(f => {
      newStatus[f.id] = 'pending';
    });
    setUploadStatus(prev => ({ ...prev, ...newStatus }));
  }, []);

  const removeFile = (fileId) => {
    setFiles(prev => {
      const file = prev.find(f => f.id === fileId);
      if (file?.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter(f => f.id !== fileId);
    });
    setUploadStatus(prev => {
      const newStatus = { ...prev };
      delete newStatus[fileId];
      return newStatus;
    });
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    
    // Mark all as uploading
    const uploadingStatus = {};
    files.forEach(f => {
      uploadingStatus[f.id] = 'uploading';
    });
    setUploadStatus(uploadingStatus);
    
    try {
      const fileList = files.map(f => f.file);
      await onUpload(fileList);
      
      // Mark all as success
      const successStatus = {};
      files.forEach(f => {
        successStatus[f.id] = 'success';
      });
      setUploadStatus(successStatus);
      
      // Clear files after successful upload
      setTimeout(() => {
        files.forEach(f => {
          if (f.preview) URL.revokeObjectURL(f.preview);
        });
        setFiles([]);
        setUploadStatus({});
      }, 2000);
    } catch {
      // Mark all as error
      const errorStatus = {};
      files.forEach(f => {
        errorStatus[f.id] = 'error';
      });
      setUploadStatus(errorStatus);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILES,
    disabled: isUploading,
  });

  const getFileIcon = (mimeType) => {
    const Icon = FILE_ICONS[mimeType] || File;
    return Icon;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-200/60 p-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-100 to-orange-100 flex items-center justify-center">
          <Upload className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Upload Documents</h2>
          <p className="text-sm text-slate-500">PRD, Figma exports, or screenshots</p>
        </div>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
          transition-all duration-200 ease-out
          ${isDragActive 
            ? 'border-indigo-400 bg-indigo-50/50 scale-[1.02]' 
            : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50/50'
          }
          ${isUploading ? 'pointer-events-none opacity-60' : ''}
        `}
      >
        <input {...getInputProps()} aria-label="File upload" />
        
        <div className={`transition-transform duration-200 ${isDragActive ? 'scale-110' : ''}`}>
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center">
            <Upload className={`w-6 h-6 text-indigo-500 ${isDragActive ? 'animate-bounce-subtle' : ''}`} />
          </div>
          
          <p className="text-slate-600 font-medium mb-1">
            {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
          </p>
          <p className="text-sm text-slate-400">
            or <span className="text-indigo-500 font-medium">browse</span> to upload
          </p>
          <p className="text-xs text-slate-400 mt-3">
            Supports PDF, DOCX, Markdown, PNG, JPG
          </p>
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-5 space-y-2">
          {files.map(({ file, id, preview }) => {
            const FileIcon = getFileIcon(file.type);
            const status = uploadStatus[id];
            
            return (
              <div
                key={id}
                className={`
                  flex items-center gap-3 p-3 rounded-xl border transition-all
                  ${status === 'success' ? 'bg-emerald-50 border-emerald-200' : 
                    status === 'error' ? 'bg-red-50 border-red-200' : 
                    'bg-slate-50 border-slate-200'}
                `}
              >
                {preview ? (
                  <img
                    src={preview}
                    alt={file.name}
                    className="w-10 h-10 rounded-lg object-cover"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                    <FileIcon className="w-5 h-5 text-slate-400" />
                  </div>
                )}
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-700 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                
                <div className="flex items-center gap-2">
                  {getStatusIcon(status)}
                  
                  {status !== 'uploading' && status !== 'success' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(id);
                      }}
                      className="p-1.5 rounded-lg hover:bg-slate-200 transition-colors"
                      aria-label={`Remove ${file.name}`}
                    >
                      <X className="w-4 h-4 text-slate-400" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && uploadProgress > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-slate-600 font-medium">Uploading...</span>
            <span className="text-indigo-600 font-medium">{uploadProgress}%</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Upload Button */}
      {files.length > 0 && !isUploading && (
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="
            w-full mt-5 py-3 px-4 rounded-xl font-medium text-white
            bg-gradient-to-r from-indigo-500 to-violet-500
            hover:from-indigo-600 hover:to-violet-600
            shadow-lg shadow-indigo-500/25
            transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
          "
        >
          Upload {files.length} {files.length === 1 ? 'file' : 'files'}
        </button>
      )}
    </div>
  );
}
