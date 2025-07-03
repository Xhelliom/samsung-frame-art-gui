"use client";
import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface UnsplashPhoto {
  id: string;
  urls: { small: string; regular: string };
  description?: string | null;
  user: { name: string; profile: string };
  download_location?: string;
}

const UnsplashSearch: React.FC<{ onSelect?: () => void }> = ({ onSelect }) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UnsplashPhoto[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.searchUnsplash(query.trim());
      setResults(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUseImage = async (url: string, id: string, filename: string) => {
    try {
      // Track download on Unsplash
      await api.trackDownload(`/photos/${id}/download`);
      
      // Download and upload to backend
      const response = await fetch(url);
      const blob = await response.blob();
      const file = new File([blob], filename, { type: 'image/jpeg' });
      
      await api.uploadImage(file);
      alert('Image téléchargée et sauvegardée localement !');
    } catch (e: any) {
      alert(e.message);
    }
  };

  // fetch featured on mount
  useEffect(() => {
    (async () => {
      try {
        const feats = await api.unsplashFeatured();
        setResults(feats);
      } catch {}
    })();
  }, []);

  return (
    <div className="w-full">
      {/* Search bar - styled like Pexels */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="relative max-w-2xl mx-auto">
          <input
            type="text"
            placeholder="Rechercher des photos gratuites"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-6 py-4 pr-16 text-lg border-2 border-gray-200 rounded-full focus:outline-none focus:border-gray-400 shadow-lg"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2 top-2 bottom-2 px-6 bg-black text-white rounded-full hover:bg-gray-800 transition flex items-center justify-center"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </div>
      </form>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      )}
      
      {error && (
        <div className="text-center py-4">
          <p className="text-red-500">{error}</p>
        </div>
      )}

      {/* Images grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {results.map((photo) => (
          <div
            key={photo.id}
            className="group relative cursor-pointer overflow-hidden rounded-lg shadow-md hover:shadow-xl transition-shadow"
            onClick={() => handleUseImage(photo.urls.regular, photo.id, `unsplash-${photo.id}.jpg`)}
          >
            <img
              src={photo.urls.small}
              alt={photo.description || "Photo Unsplash"}
              className="w-full h-64 object-cover group-hover:scale-105 transition-transform duration-300"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors duration-300 flex items-end">
              <div className="p-4 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <p className="text-sm font-medium">Photo by {photo.user.name}</p>
                <p className="text-xs opacity-75">Cliquer pour télécharger</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UnsplashSearch; 