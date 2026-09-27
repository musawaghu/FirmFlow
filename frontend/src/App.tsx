import { Navigate, Route, Routes } from "react-router-dom";

import { RequireRole } from "./components/RequireRole";
import { ScrollToTop } from "./components/ScrollToTop";
import { AdminDashboard } from "./pages/admin/AdminDashboard";
import { AdminLayout } from "./pages/admin/AdminLayout";
import { AdminModule } from "./pages/admin/AdminModule";
import { ManualReview } from "./pages/admin/ManualReview";
import { Manuals } from "./pages/admin/Manuals";
import { Ask } from "./pages/employee/Ask";
import { EmployeeHome } from "./pages/employee/EmployeeHome";
import { EmployeeLayout } from "./pages/employee/EmployeeLayout";
import { FinalCheck } from "./pages/employee/FinalCheck";
import { ModulePage } from "./pages/employee/ModulePage";
import { Landing } from "./pages/Landing";

export function App() {
  return (
    <>
      <ScrollToTop />
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
        <Route path="final-check" element={<FinalCheck />} />
        <Route path="ask" element={<Ask />} />
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
        <Route path="manuals" element={<Manuals />} />
        <Route path="manuals/:manualId" element={<ManualReview />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
