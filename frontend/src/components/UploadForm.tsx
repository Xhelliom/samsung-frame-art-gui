"use client";
import React, { useRef, useState } from "react";
import { api } from "@/lib/api";

const UploadForm: React.FC<{ onUploaded?: () => void }> = ({ onUploaded }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadImage(file);
      onUploaded?.();
      if (inputRef.current) inputRef.current.value = "";
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg p-6 border-2 border-dashed border-gray-300 hover:border-gray-400 transition-colors">
      <div className="text-center">
        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Téléverser une image</h3>
        <p className="text-sm text-gray-600 mb-4">Glissez-déposez votre image ou cliquez pour parcourir</p>
        <label className="cursor-pointer">
          <input
            type="file"
            accept="image/jpeg,image/png"
            ref={inputRef}
            onChange={handleFileChange}
            disabled={uploading}
            className="hidden"
          />
          <span className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-black hover:bg-gray-800 transition">
            {uploading ? "Envoi en cours..." : "Choisir un fichier"}
          </span>
        </label>
        {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      </div>
    </div>
  );
};

export default UploadForm; 