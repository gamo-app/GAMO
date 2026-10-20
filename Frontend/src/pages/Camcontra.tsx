//import { cambiarcontraseña } from "../database/Api";
import Header from "../components/Header";
import Main from "../components/Main";
import Icon from "../components/Icon";
import { Link,useNavigate } from "react-router-dom";
import { confirmar } from "../components/Alerta";
import { useRef, useEffect } from "react";
import Confetti, { type ConfettiRef } from "../components/Confetti";
function Camcontra() {
  const confetti = useRef<ConfettiRef>(null);
const navigate = useNavigate();
  useEffect(() => {
    confetti.current?.aparecer();
  }, []);
  return (
    <Main>
      <Header salir />
  <Confetti ref={confetti} />
      <section className="centro2">
        <div className="listabloques">

        <div className="bloque espaciado">
          <div className="listay">
         
            <Icon tipo={22} tamaño={13} />
<h3 className="centro">¡Te damos la bienvenida!</h3>
<p className="centro">Por seguridad, es necesario que cambies tu contraseña para continuar.</p>
</div>
<br />
          <div className="input">
          <label htmlFor="Password">
                        Nueva contraseña
                      </label>

                      <input
                        id="Password"
                        className="blanco"
                        type="password"
                        placeholder="-----"
                      />
        </div>
        <div className="input">
          <label htmlFor="confirmarPassword">
                        Confirme su contraseña
                      </label>

                      <input
                        id="confirmarPassword"
                        className="blanco"
                        type="password"
                        placeholder="-----"
                      />
        </div>

<div className="divisorx">
<button
  className="rojo"
  onClick={(e) => {
    e.preventDefault();

   confirmar(
  "Si salís ahora, tendrás que cambiar tu contraseña la próxima vez que ingreses. ¿Querés continuar?",
  () => {
    navigate("/home");
  }
);
  }}
>
  Mantener
</button>
<Link to="/home"  className="azul">
        Cambiar
        </Link>
       
</div>
      

        </div>
        </div>
      </section>
  </Main>
  );
}

export default Camcontra;