
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function RutaProtegida() {
  const { usuario, cargando } = useAuth();

  if (cargando) {
    return <p>Verificando sesión...</p>;
  }

  if (!usuario) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

export default RutaProtegida;
