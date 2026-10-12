import Icon from "./Icon";
import { useLocation, useNavigate } from "react-router-dom";

function Header() {
  const location = useLocation();
  const navigate = useNavigate();


  return (
    <header className={location.pathname === "/" || location.pathname === "/crear" ? "login" : ""}>
      {location.pathname === "/escanear" ? (
        <h1>Escanea el QR</h1>
      ) : location.pathname === "/horarios" ? (
        <h1>
          Mis <br /> Horarios
        </h1>
      ) : location.pathname === "/home" ? (
        <h1>
          Bienvenido <br /> Luciano
        </h1>
      ) : location.pathname === "/buscar" ? (
        <h1>
          Buscar
        </h1>
      ) : location.pathname === "/usuario" ? (
        <h1>
          Mi <br /> usuario
        </h1>
      ) : location.pathname === "/socios" ? (
        <h1>
          Mis <br /> Socios
        </h1>
      ) : <></>
    }

      {location.pathname === "/escanear" ? (
        <button onClick={() => navigate(-1)}>
          Cancelar
        </button>
      ) : location.pathname === "/"  || location.pathname === "/crear" ? (
        <>
        <Icon tipo={10} tamaño={23} />
        <p>Gestión para centros deportivos</p>
        </>
      )  : (
        <Icon tipo={9} tamaño={6.6} />
      )}
    </header>
  );
}

export default Header;