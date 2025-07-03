import React, { useState } from "react";
import { api } from "@/lib/api";

interface DebugResult {
  [key: string]: any;
}

const DebugPanel: React.FC = () => {
  const [results, setResults] = useState<{ [key: string]: DebugResult }>({});
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({});

  const executeDebugCommand = async (command: string, fn: () => Promise<any>) => {
    setLoading(prev => ({ ...prev, [command]: true }));
    try {
      const result = await fn();
      setResults(prev => ({ ...prev, [command]: result }));
    } catch (error: any) {
      setResults(prev => ({ ...prev, [command]: { error: error.message } }));
    } finally {
      setLoading(prev => ({ ...prev, [command]: false }));
    }
  };

  const debugCommands = [
    {
      title: "Version API",
      command: "api-version",
      description: "Récupère la version de l'API Samsung (ancienne < 4.0.0.0)",
      fn: () => api.debugApiVersion(),
    },
    {
      title: "Statut TV Complet",
      command: "tv-status",
      description: "Statut complet de la TV (allumée, Art Mode, orientation, etc.)",
      fn: () => api.debugTvStatus(),
    },
    {
      title: "Images Disponibles",
      command: "available-art",
      description: "Liste toutes les images disponibles sur la TV",
      fn: () => api.debugAvailableArt(),
    },
    {
      title: "Paramètres Art Mode",
      command: "artmode-settings",
      description: "Récupère les paramètres Art Mode (luminosité, etc.)",
      fn: () => api.debugArtModeSettings(),
    },
    {
      title: "Statut Slideshow",
      command: "slideshow-status",
      description: "Statut du slideshow (ancienne et nouvelle API)",
      fn: () => api.debugSlideshowStatus(),
    },
    {
      title: "Informations Appareil",
      command: "device-info",
      description: "Informations détaillées sur la TV",
      fn: () => api.debugDeviceInfo(),
    },
    {
      title: "Liste Applications",
      command: "app-list",
      description: "Liste toutes les applications installées",
      fn: () => api.debugAppList(),
    },
  ];

  const [selectedFile, setSelectedFile] = useState("");
  const [artMode, setArtMode] = useState<"on" | "off">("on");
  const [selectedKey, setSelectedKey] = useState("KEY_POWER");
  const [selectedApp, setSelectedApp] = useState("");

  const commonKeys = [
    "KEY_POWER", "KEY_POWEROFF", "KEY_HOME", "KEY_MENU", "KEY_BACK",
    "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT", "KEY_ENTER",
    "KEY_VOLUP", "KEY_VOLDOWN", "KEY_MUTE", "KEY_CHUP", "KEY_CHDOWN",
    "KEY_SOURCE", "KEY_HDMI", "KEY_NETFLIX", "KEY_AMAZON"
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-6">Panneau de Debug TV</h2>
        
        {/* Commandes de base */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {debugCommands.map(({ title, command, description, fn }) => (
            <div key={command} className="border rounded-lg p-4">
              <h3 className="font-semibold mb-2">{title}</h3>
              <p className="text-sm text-gray-600 mb-3">{description}</p>
              <button
                onClick={() => executeDebugCommand(command, fn)}
                disabled={loading[command]}
                className={`px-4 py-2 rounded text-white font-medium ${
                  loading[command] 
                    ? "bg-gray-400 cursor-not-allowed" 
                    : "bg-blue-600 hover:bg-blue-700"
                }`}
              >
                {loading[command] ? "Chargement..." : "Exécuter"}
              </button>
            </div>
          ))}
        </div>

        {/* Contrôles TV */}
        <div className="border rounded-lg p-4 mb-6">
          <h3 className="font-semibold mb-4">Contrôles TV</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Allumer TV */}
            <div>
              <button
                onClick={() => executeDebugCommand("power-on", () => api.debugPowerOn())}
                disabled={loading["power-on"]}
                className={`w-full px-4 py-2 rounded text-white font-medium ${
                  loading["power-on"] 
                    ? "bg-gray-400 cursor-not-allowed" 
                    : "bg-green-600 hover:bg-green-700"
                }`}
              >
                {loading["power-on"] ? "Allumage..." : "🔌 Allumer TV"}
              </button>
            </div>
            
            {/* Envoyer touche */}
            <div>
              <div className="flex space-x-2">
                <select
                  value={selectedKey}
                  onChange={(e) => setSelectedKey(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded text-sm"
                >
                  {commonKeys.map(key => (
                    <option key={key} value={key}>{key.replace('KEY_', '')}</option>
                  ))}
                </select>
                <button
                  onClick={() => executeDebugCommand("send-key", () => api.debugSendKey(selectedKey))}
                  disabled={loading["send-key"]}
                  className={`px-4 py-2 rounded text-white font-medium ${
                    loading["send-key"] 
                      ? "bg-gray-400 cursor-not-allowed" 
                      : "bg-orange-600 hover:bg-orange-700"
                  }`}
                >
                  {loading["send-key"] ? "Envoi..." : "📺 Envoyer"}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Contrôles Art Mode */}
        <div className="border rounded-lg p-4 mb-6">
          <h3 className="font-semibold mb-4">Contrôles Art Mode</h3>
          <div className="flex items-center space-x-4">
            <select
              value={artMode}
              onChange={(e) => setArtMode(e.target.value as "on" | "off")}
              className="px-3 py-2 border rounded"
            >
              <option value="on">Activer</option>
              <option value="off">Désactiver</option>
            </select>
            <button
              onClick={() => executeDebugCommand("set-artmode", () => api.debugSetArtMode(artMode))}
              disabled={loading["set-artmode"]}
              className={`px-4 py-2 rounded text-white font-medium ${
                loading["set-artmode"] 
                  ? "bg-gray-400 cursor-not-allowed" 
                  : "bg-green-600 hover:bg-green-700"
              }`}
            >
              {loading["set-artmode"] ? "Chargement..." : "Changer Art Mode"}
            </button>
          </div>
        </div>

        {/* Test d'upload */}
        <div className="border rounded-lg p-4 mb-6">
          <h3 className="font-semibold mb-4">Test d'Upload</h3>
          <div className="flex items-center space-x-4">
            <input
              type="text"
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              placeholder="Nom du fichier (ex: image.jpg)"
              className="flex-1 px-3 py-2 border rounded"
            />
            <button
              onClick={() => executeDebugCommand("test-upload", () => api.debugTestUpload(selectedFile))}
              disabled={loading["test-upload"] || !selectedFile}
              className={`px-4 py-2 rounded text-white font-medium ${
                loading["test-upload"] || !selectedFile
                  ? "bg-gray-400 cursor-not-allowed" 
                  : "bg-red-600 hover:bg-red-700"
              }`}
            >
              {loading["test-upload"] ? "Test..." : "Tester Upload"}
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Teste l'upload avec logs détaillés pour diagnostiquer les erreurs
          </p>
        </div>

        {/* Lancement d'application */}
        <div className="border rounded-lg p-4 mb-6">
          <h3 className="font-semibold mb-4">Lancement d'Application</h3>
          <div className="flex items-center space-x-4">
            <input
              type="text"
              value={selectedApp}
              onChange={(e) => setSelectedApp(e.target.value)}
              placeholder="ID Application (ex: 3201606009684 pour Spotify)"
              className="flex-1 px-3 py-2 border rounded"
            />
            <button
              onClick={() => executeDebugCommand("run-app", () => api.debugRunApp(selectedApp))}
              disabled={loading["run-app"] || !selectedApp}
              className={`px-4 py-2 rounded text-white font-medium ${
                loading["run-app"] || !selectedApp
                  ? "bg-gray-400 cursor-not-allowed" 
                  : "bg-purple-600 hover:bg-purple-700"
              }`}
            >
              {loading["run-app"] ? "Lancement..." : "🚀 Lancer App"}
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Utilisez d'abord "Liste Applications" pour voir les IDs disponibles
          </p>
        </div>
      </div>

      {/* Résultats */}
      {Object.keys(results).length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">Résultats</h3>
          <div className="space-y-4">
            {Object.entries(results).map(([command, result]) => (
              <div key={command} className="border rounded-lg p-4">
                <h4 className="font-semibold mb-2 capitalize">{command.replace("-", " ")}</h4>
                <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Aide */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-3">💡 Guide d'utilisation</h3>
        <div className="space-y-2 text-sm">
          <p><strong>1. Version API :</strong> Vérifiez si votre TV utilise l'ancienne API (&lt; 4.0.0.0)</p>
          <p><strong>2. Statut TV :</strong> Vérifiez que la TV est allumée et supporte l'Art Mode</p>
          <p><strong>3. Test Upload :</strong> Testez l'upload d'un fichier spécifique avec logs détaillés</p>
          <p><strong>4. Art Mode :</strong> Activez/désactivez l'Art Mode directement</p>
          <p><strong>5. Images Disponibles :</strong> Voir toutes les images sur la TV</p>
        </div>
      </div>
    </div>
  );
};

export default DebugPanel; 