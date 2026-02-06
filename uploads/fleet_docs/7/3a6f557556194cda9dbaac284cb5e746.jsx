import { Routes, Route, Navigate } from "react-router-dom";

/* Auth */
import Register from "./features/auth/Register.jsx";
import Login from "./features/auth/Login.jsx";

/* Rider */
import Home from "./features/rider/pages/Home.jsx";
import BookRide from "./features/rider/components/BookRide.jsx";
import TripTracking from "./features/rider/components/TripTracking.jsx";

/* Driver */
import DriverDashboard from "./features/driver/pages/DriverDashboard.jsx";

/* Admin */
import AdminLayout from "./features/admin/AdminLayout.jsx";
import AdminLogin from "./features/admin/AdminLogin.jsx";
import TenantManager from "./features/admin/TenantManager.jsx";

/* Fleet */
import FleetRegistration from "./features/fleet/FleetRegistration.jsx";
import FleetDashboard from "./features/fleet/FleetDashboard.jsx";

import TenantDashboard from "./features/tenant/TenantDashboard.jsx";

function App() {
  return (
    <Routes>
      {/* Root */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* ================= AUTH ================= */}
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />

      {/* ================= RIDER ================= */}
      <Route path="/rider">
        <Route index element={<Navigate to="home" replace />} />
        <Route path="home" element={<Home />} />
        <Route path="book" element={<BookRide />} />
        <Route path="trip/:tripId" element={<TripTracking />} />
      </Route>


      {/* ================= DRIVER ================= */}
      <Route path="/driver" element={<DriverDashboard />} />
      <Route path="/driver-dashboard" element={<Navigate to="/driver" replace />} />

      {/* ================= FLEET ================= */}
      <Route path="/fleet-registration" element={<FleetRegistration />} />
      <Route path="/dashboard" element={<FleetDashboard />} />

      {/* ================= ADMIN ================= */}
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="tenants" replace />} />
        <Route path="tenants" element={<TenantManager />} />
      </Route>

      {/* ================= TENANT ADMIN ================= */}
      <Route path="/tenant-admin-dashboard" element={<TenantDashboard />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
