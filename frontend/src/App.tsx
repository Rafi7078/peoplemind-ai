import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
function App() {
  return (
    <Routes>
      <Route
        element={<LoginPage />}
        path="/login"
      />
      <Route element={<ProtectedRoute />}>
        <Route
          element={<DashboardPage />}
          path="/"
        />
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
