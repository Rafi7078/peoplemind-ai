import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { CVIntelligencePage } from "./pages/CVIntelligencePage";
import { DocumentAssistantPage } from "./pages/DocumentAssistantPage";
import { LoginPage } from "./pages/LoginPage";
function App() {
  return (
    <Routes>
      <Route
        element={<LoginPage />}
        path="/login"
      />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route
            element={<DashboardPage />}
            index
          />
          <Route
            element={
              <DocumentAssistantPage />
            }
            path="documents"
          />
          <Route
            element={
              <CVIntelligencePage />
            }
            path="cv-intelligence"
          />
        </Route>
      </Route>
      <Route
        element={
          <Navigate
            replace
            to="/"
          />
        }
        path="*"
      />
    </Routes>
  );
}
export default App;
