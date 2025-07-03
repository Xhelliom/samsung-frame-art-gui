"use client";
import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface CurrentArtData {
  content_id?: string;
  thumbnail?: string;
  thumbnail_format?: string;
  [key: string]: any;
}

const CurrentArt: React.FC = () => {
  const [currentArt, setCurrentArt] = useState<CurrentArtData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchCurrentArt = async () => {
    try {
      const data = await api.getCurrentImage();
      setCurrentArt(data);
    } catch (error) {
      console.error("Erreur lors de la récupération de l'image actuelle:", error);
      setCurrentArt(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentArt();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="animate-pulse">
          <div className="h-64 bg-gray-300 rounded-lg mb-4"></div>
          <div className="h-4 bg-gray-300 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (!currentArt || currentArt.status === "no_current_image") {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Image actuelle</h2>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">
            {currentArt?.message || "Aucune image actuellement affichée"}
          </p>
          <button
            onClick={fetchCurrentArt}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Actualiser
          </button>
        </div>
      </div>
    );
  }

  if (currentArt.status === "no_art_mode") {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Image actuelle</h2>
        <div className="text-center py-8">
          <p className="text-orange-600 mb-4">
            {currentArt.message || "La TV n'est pas en Art Mode"}
          </p>
          <p className="text-gray-500 text-sm mb-4">
            Activez l'Art Mode sur votre TV pour voir l'image actuelle
          </p>
          <button
            onClick={fetchCurrentArt}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Actualiser
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      <h2 className="text-xl font-semibold mb-4">Image actuelle</h2>
      {currentArt.thumbnail && (
        <div className="mb-4">
          <img
            src={`data:image/${currentArt.thumbnail_format || 'jpeg'};base64,${currentArt.thumbnail}`}
            alt="Thumbnail de l'image actuelle"
            className="w-full h-64 object-cover rounded-lg"
          />
        </div>
      )}
      <div className="space-y-2">
        <p><strong>ID:</strong> {currentArt.content_id}</p>
        {currentArt.title && <p><strong>Titre:</strong> {currentArt.title}</p>}
        {currentArt.artist && <p><strong>Artiste:</strong> {currentArt.artist}</p>}
        <button
          onClick={fetchCurrentArt}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Actualiser
        </button>
      </div>
    </div>
  );
};

export default CurrentArt; 