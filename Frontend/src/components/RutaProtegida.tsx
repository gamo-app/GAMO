
import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { obtenerSesion } from "../database/Api";

export default function RutaProtegida() {
  const [autenticado, setAutenticado] = useState<boolean | null>(null);
  const location = useLocation();

  useEffect(() => {
    let activo = true;

    async function verificarSesion() {
      try {
        const sesion = await obtenerSesion();

        if (activo) {
          setAutenticado(sesion.autenticado === true);
        }
      } catch {
        if (activo) {
          setAutenticado(false);
        }
      }
    }

    verificarSesion();

    return () => {
      activo = false;
    };
  }, []);

  if (autenticado === null) {
    return <p>Verificando sesión...</p>;
  }

  if (!autenticado) {
    return (
      <Navigate
        to="/"
        replace
        state={{ from: location }}
      />
    );
  }

  return <Outlet />;
}
