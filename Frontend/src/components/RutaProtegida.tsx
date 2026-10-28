
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { PermisosUsuario } from "../api/Socios";

type Props = {
  permiso?: keyof PermisosUsuario;
};

function RutaProtegida({ permiso }: Props) {
  const { usuario, cargando } = useAuth();

  if (cargando) {
    return(
    <div className="alerta-fondo">
      <img
        src="/cargando.svg"
        alt="Cargando..."
        className="cargando"
      />
    </div>
    ) ;
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
