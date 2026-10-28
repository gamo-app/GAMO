
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { PermisosUsuario } from "../api/Socios";

type Props = {
  permiso?: keyof PermisosUsuario;
};

function RutaProtegida({ permiso }: Props) {
  const { usuario, cargando } = useAuth();

  if (cargando) {
    return <p>Verificando sesión...</p>;
  }

  if (!usuario) {
    return <Navigate to="/" replace />;
  }

  if (
    permiso &&
    usuario.rol?.permisos?.[permiso] != true
  ) {
    return <Navigate to="/home" replace />;
  }

  return <Outlet />;
}

export default RutaProtegida;
