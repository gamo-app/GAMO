import Icon from "../components/Icon";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function NavBar() {
  const { usuario } = useAuth();
  const esSocio = usuario?.rol?.nombre.toLocaleLowerCase() === "socio";

  return (
    <footer>
       <div className="pc contenedorazul">
          <Icon tipo={10} tamaño={14} />
        </div>
      <NavLink to="/home" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={0} tamaño={3}  color={isActive ? 1 : 0} />
            Home
          </>
        )}
      </NavLink>

      <NavLink to="/horarios" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={1} tamaño={3}  color={isActive ? 1 : 0} />
            Horarios
          </>
        )}
      </NavLink>

      <NavLink to="/escanear" className="escanear">
        <Icon tipo={4} color={2} tamaño={3} />
      </NavLink>

      {esSocio ? (
        <NavLink to="/buscar" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={3} tamaño={3}  color={isActive ? 1 : 0} />
            Buscar
          </>
        )}
      </NavLink>
      ) : (
        <NavLink to="/gestion" className="icono">
          {({ isActive }) => (
            <>
              <Icon tipo={11} tamaño={3} color={isActive ? 1 : 0} />
              Gestión
            </>
          )}
        </NavLink>
      )}

      <NavLink to="/buscar" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={3} tamaño={3}  color={isActive ? 1 : 0} />
            Buscar
          </>
        )}
      </NavLink>
    </footer>
  );
}

export default NavBar;