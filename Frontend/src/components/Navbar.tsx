import Icon from "../components/Icon";
import { NavLink } from "react-router-dom";

function NavBar() {
  let rol = "Admin"
  return (
    <footer>
      <NavLink to="/home" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={0} color={isActive ? 1 : 0} />
            Home
          </>
        )}
      </NavLink>

      <NavLink to="/horarios" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={1} color={isActive ? 1 : 0} />
            Horarios
          </>
        )}
      </NavLink>

      <NavLink to="/escanear" className="escanear">
        <Icon tipo={4} color={2} tamaño={2.5} />
      </NavLink>

     {rol != "socio" ? <NavLink to="/socios" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={11} color={isActive ? 1 : 0} />
            Socios
          </>
        )}
      </NavLink>
      : (
         <NavLink to="/buscar" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={3} color={isActive ? 1 : 0} />
            Buscar
          </>
        )}
      </NavLink>
      )}

      <NavLink to="/usuario" className="icono">
        {({ isActive }) => (
          <>
            <Icon tipo={2} color={isActive ? 1 : 0} />
            Usuario
          </>
        )}
      </NavLink>
    </footer>
  );
}

export default NavBar;