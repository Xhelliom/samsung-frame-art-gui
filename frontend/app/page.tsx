"use client";

import { useState, useEffect } from "react";
import ImageGrid from "@/components/ImageGrid";
import UploadForm from "@/components/UploadForm";
import UnsplashSearch from "@/components/UnsplashSearch";
import CurrentArt from "@/components/CurrentArt";
import DebugPanel from "@/components/DebugPanel";

type Tab = "local" | "unsplash" | "debug";

export default function Home() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [tab, setTab] = useState<Tab>("unsplash");

  const triggerRefresh = () => setRefreshKey((k) => k + 1);

  return (
    <div className="min-h-screen relative z-10">
      {/* Header */}
      <header className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <h1 className="text-2xl font-bold text-gray-900">Frame Art</h1>
          <nav className="hidden md:flex items-center gap-6">
            <button
              onClick={() => setTab("unsplash")}
              className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                tab === "unsplash" 
                  ? "bg-black text-white" 
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              Découvrir
            </button>
            <button
              onClick={() => setTab("local")}
              className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                tab === "local" 
                  ? "bg-black text-white" 
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              Mes images
            </button>
            <button
              onClick={() => setTab("debug")}
              className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                tab === "debug" 
                  ? "bg-black text-white" 
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              Debug
            </button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 py-16 text-center">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Les plus belles images pour votre
            <br />
            Samsung Frame TV
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Découvrez et envoyez des images exceptionnelles directement sur votre téléviseur
          </p>
          
          {/* Search bar for Unsplash */}
          {tab === "unsplash" && (
            <div className="max-w-2xl mx-auto">
              <UnsplashSearch onSelect={triggerRefresh} />
            </div>
          )}
        </div>
      </section>

      {/* Current Art Display */}
      <CurrentArt />

      {/* Content based on tab */}
      <main className="px-6 pb-16">
        <div className="max-w-7xl mx-auto">
          {tab === "local" && (
            <div>
              <div className="mb-8">
                <UploadForm onUploaded={triggerRefresh} />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Vos images</h3>
              <ImageGrid key={refreshKey} />
            </div>
          )}

          {tab === "unsplash" && (
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-6">Photos populaires</h3>
              {/* UnsplashSearch component will show featured images */}
            </div>
          )}

          {tab === "debug" && (
            <div className="space-y-8">
              <DebugPanel />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}