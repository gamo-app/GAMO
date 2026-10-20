
import Icon from "./Icon";
import {  useNavigate, Link } from "react-router-dom";
import { storage } from "../database/Storage";
import { confirmar } from "../components/Alerta";
function Header({ atras = false, login= false,salir=false }) {
  const navigate = useNavigate();

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
            className="circuloazul2"
            onClick={() => navigate(-1)}
          >
            <Icon tipo={18} tamaño={2} />
          </button>
        </>
      ) : salir ? (
        <>
          <Icon tipo={10} tamaño={14} />

        <button   className="circuloazul2"  onClick={ (e)=>{
                       e.preventDefault();
        
                  confirmar(
                  "Vas a cerrar la sesión actual ¿Querés continuar?",
                  () => {
                    navigate("/");
                    storage.clear();
                  })
                    }
        
                    }>
 <Icon tipo={18} tamaño={2} />
        </button>
        </>

      ) : (
        <>
          <Icon tipo={10} tamaño={14} />
          <Link to="/noti">
            <Icon tipo={19} tamaño={3.2} />
          </Link>
        </>
      )}
    </header>
  );
}

export default Header;
