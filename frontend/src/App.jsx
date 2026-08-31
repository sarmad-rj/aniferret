import { Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./components/landing/LandingPage";
import AppLayout from "./components/app/AppLayout";
import DiscoverPage from "./components/app/DiscoverPage";
import DossiersPage from "./components/app/DossiersPage";
import LoreAssistantPage from "./components/app/LoreAssistantPage";
import WatchOrderPage from "./components/app/WatchOrderPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/app" element={<AppLayout />}>
        <Route index element={<Navigate to="dossiers" replace />} />
        <Route path="discover" element={<DiscoverPage />} />
        <Route path="dossiers" element={<DossiersPage />} />
        <Route path="lore-assistant" element={<LoreAssistantPage />} />
        <Route path="watch-order" element={<WatchOrderPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
