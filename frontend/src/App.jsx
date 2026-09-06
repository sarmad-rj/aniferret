import { Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./components/landing/LandingPage";
import AppLayout from "./components/app/AppLayout";
import DiscoverPage from "./components/app/DiscoverPage";
import DossiersPage from "./components/app/DossiersPage";
import LoreAssistantPage from "./components/app/LoreAssistantPage";
import WatchOrderPage from "./components/app/WatchOrderPage";
import ProfilePage from "./components/app/ProfilePage";
import VerifyEmail from "./components/VerifyEmail";
import ResetPassword from "./components/ResetPassword";
import AdminLayout from "./components/admin/AdminLayout";
import AdminOverviewPage from "./components/admin/AdminOverviewPage";
import AdminAnimePage from "./components/admin/AdminAnimePage";
import AdminAnimeDetailPage from "./components/admin/AdminAnimeDetailPage";
import AdminUsersPage from "./components/admin/AdminUsersPage";
import AdminDataIntegrityPage from "./components/admin/AdminDataIntegrityPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/app" element={<AppLayout />}>
        <Route index element={<Navigate to="dossiers" replace />} />
        <Route path="discover" element={<DiscoverPage />} />
        <Route path="dossiers" element={<DossiersPage />} />
        <Route path="lore-assistant" element={<LoreAssistantPage />} />
        <Route path="watch-order" element={<WatchOrderPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="overview" replace />} />
        <Route path="overview" element={<AdminOverviewPage />} />
        <Route path="anime" element={<AdminAnimePage />} />
        <Route path="anime/:animeId" element={<AdminAnimeDetailPage />} />
        <Route path="users" element={<AdminUsersPage />} />
        <Route path="data-integrity" element={<AdminDataIntegrityPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
