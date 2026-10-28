import { memo } from "react";
import { Link, useNavigate } from "react-router-dom";

import Icon from "./Icon";
import { confirmar } from "../components/Alerta";
import { useAuth } from "../context/AuthContext";

type HeaderProps = {
  atras?: boolean;
  login?: boolean;
  salir?: boolean;
};

function Header({
  atras = false,
  login = false,
  salir = false,
}: HeaderProps) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  function confirmarCierreSesion() {
    confirmar(
      "Vas a cerrar la sesión actual. ¿Querés continuar?",
      () => {
        void logout()
          .then(() => navigate("/", { replace: true }))
          .catch((error: unknown) => {
            console.error("Error al cerrar sesión:", error);
          });
      }
    );
  }

  return (
    <header className={login ? "login" : ""}>
      {login ? (
        <>
          <Icon tipo={10} tamaño={23} />
          <p style={{ marginTop: "0.5vh" }}>
            Gestión para centros deportivos
          </p>
        </>
      ) : atras ? (
        <>
          <Icon tipo={10} tamaño={14} />
          <button
            type="button"
            className="circuloazul2"
            onClick={() => navigate(-1)}
          >
            <Icon tipo={18} tamaño={2} />
          </button>
        </>
      ) : salir ? (
        <>
          <Icon tipo={10} tamaño={14} />
          <button
            type="button"
            className="circuloazul2"
            onClick={confirmarCierreSesion}
            aria-label="Cerrar sesión"
          >
            <Icon tipo={18} tamaño={2} />
          </button>
        </>
      ) : (
        <>
          <Icon tipo={10} tamaño={14} />
          <Link to="/notificacion">
            <Icon tipo={19} tamaño={3.2} />
          </Link>
        </>
      )}
    </header>
  );
}

export default memo(Header);