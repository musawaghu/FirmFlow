import { Navigate, Route, Routes } from "react-router-dom";

import { RequireRole } from "./components/RequireRole";
import { AdminDashboard } from "./pages/admin/AdminDashboard";
import { AdminLayout } from "./pages/admin/AdminLayout";
import { AdminModule } from "./pages/admin/AdminModule";
import { EmployeeHome } from "./pages/employee/EmployeeHome";
import { EmployeeLayout } from "./pages/employee/EmployeeLayout";
import { ModulePage } from "./pages/employee/ModulePage";
import { Landing } from "./pages/Landing";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route
        path="/app"
        element={
          <RequireRole role="employee">
            <EmployeeLayout />
          </RequireRole>
        }
      >
        <Route index element={<EmployeeHome />} />
        <Route path="modules/:moduleId" element={<ModulePage />} />
      </Route>
      <Route
        path="/admin"
        element={
          <RequireRole role="admin">
            <AdminLayout />
          </RequireRole>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="modules/:layer/:moduleId" element={<AdminModule />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
