"use client";
import React, { useEffect, useState } from "react";
import { api, ImageItem } from "@/lib/api";

const ImageGrid: React.FC = () => {
  const [images, setImages] = useState<ImageItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchImages = async () => {
    setLoading(true);
    try {
      const data = await api.listImages();
      setImages(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  const handleSendToTV = async (filename: string) => {
    try {
      const updatedImage = await api.sendToTV(filename);
      // Refresh the images list to show the updated state
      fetchImages();
      alert("Image envoyée à la TV !");
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleApplyArt = async (remote?: string | null) => {
    if (!remote) return;
    try {
      await api.setImage(remote);
      alert("Image appliquée en Art Mode !");
    } catch (e: any) {
      alert(e.message);
    }
  };

  const IMG_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  if (loading) {
    return <div>Chargement…</div>;
  }

  if (error) {
    return <div className="text-red-500">Erreur: {error}</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {images.map((img) => (
        <div key={img.file} className="group relative overflow-hidden rounded-lg shadow-md hover:shadow-xl transition-shadow">
          <img
            src={`${IMG_BASE}/images/${img.file}`}
            alt={img.file}
            className="w-full h-64 object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors duration-300 flex items-center justify-center">
            {!img.remote_filename ? (
              <button
                className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 px-6 py-2 bg-blue-600 text-white rounded-full font-medium hover:bg-blue-700"
                onClick={() => handleSendToTV(img.file)}
              >
                Envoyer à la TV
              </button>
            ) : (
              <button
                className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 px-6 py-2 bg-green-600 text-white rounded-full font-medium hover:bg-green-700"
                onClick={() => handleApplyArt(img.remote_filename!)}
              >
                Appliquer Art
              </button>
            )}
          </div>
          
          {/* Status badge */}
          <div className="absolute top-2 right-2">
            {img.remote_filename ? (
              <div className="bg-green-500 text-white px-2 py-1 rounded text-xs">
                Sur la TV
              </div>
            ) : (
              <div className="bg-orange-500 text-white px-2 py-1 rounded text-xs">
                Local uniquement
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ImageGrid;
