import Icon from "./Icon";
import { useLocation, useNavigate,Link } from "react-router-dom";


function Header() {
  const location = useLocation();
  const navigate = useNavigate();


  return (
    <header className={location.pathname === "/" || location.pathname === "/crear" ? "login" : ""}>
     

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
        <>
       <Icon tipo={10} tamaño={14} />
       
       <Link to="/noti" ><Icon tipo={19} tamaño={2.4} /></Link>
       </>
      )}
       
    </header>
  );
}

export default Header;