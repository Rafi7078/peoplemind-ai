import {
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";
import { useAuth } from "./auth/useAuth";
import {
  AppShell,
} from "./components/AppShell";
import {
  ProtectedRoute,
} from "./components/ProtectedRoute";
import {
  AttendanceManagementPage,
} from "./pages/AttendanceManagementPage";
import {
  CVIntelligencePage,
} from "./pages/CVIntelligencePage";
import {
  DashboardPage,
} from "./pages/DashboardPage";
import {
  DocumentAssistantPage,
} from "./pages/DocumentAssistantPage";
import {
  EmployeeDailyAttendancePage,
} from "./pages/EmployeeDailyAttendancePage";
import {
  LoginPage,
} from "./pages/LoginPage";
function AdminRoute() {
  const {
    user,
  } = useAuth();
  if (!user?.is_admin) {
    return (
      <Navigate
        replace
        to="/attendance"
      />
    );
  }
  return <Outlet />;
}
function HomeRoute() {
  const {
    user,
  } = useAuth();
  if (!user?.is_admin) {
    return (
      <Navigate
        replace
        to="/attendance"
      />
    );
  }
  return <DashboardPage />;
}
function AttendanceRoute() {
  const {
    user,
  } = useAuth();
  if (user?.is_admin) {
    return (
      <AttendanceManagementPage />
    );
  }
  return (
    <EmployeeDailyAttendancePage />
  );
}
function App() {
  return (
    <Routes>
      <Route
        element={<LoginPage />}
        path="/login"
      />
      <Route
        element={<ProtectedRoute />}
      >
        <Route
          element={<AppShell />}
        >
          <Route
            element={<HomeRoute />}
            index
          />
          <Route
            element={
              <AttendanceRoute />
            }
            path="attendance"
          />
          <Route
            element={<AdminRoute />}
          >
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
