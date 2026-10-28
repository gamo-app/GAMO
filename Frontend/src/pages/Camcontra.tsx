
import Icon from "../components/Icon";
import { useNavigate } from "react-router-dom";
import { confirmar } from "../utils/confirmar";
import { useRef, useEffect, useState } from "react";
import Confetti, { type ConfettiRef } from "../components/Confetti";

function Camcontra() {
  const confetti = useRef<ConfettiRef>(null);
  const navigate = useNavigate();

  const [contrasena, setContrasena] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    confetti.current?.aparecer();
  }, []);

  function handleCambiar() {
    setError("");

    if (contrasena.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }

    if (contrasena !== confirmacion) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    // Acá debe llamarse al endpoint que cambia la contraseña.
  }

  return (
    <>
      <Confetti ref={confetti} />

      <section className="centro2">
        <div className="listabloques">
          <div className="bloque espaciado">
            <div className="listay">
              <Icon tipo={22} tamaño={13} />
              <h3 className="centro">¡Te damos la bienvenida!</h3>
              <p className="centro">
                Por seguridad, es necesario que cambies tu contraseña
                para continuar.
              </p>
            </div>

            <br />

            <div className="input">
              <label htmlFor="Password">Nueva contraseña</label>
              <input
                id="Password"
                className="blanco"
                type="password"
                autoComplete="new-password"
                placeholder="Nueva contraseña"
                value={contrasena}
                onChange={(e) => setContrasena(e.target.value)}
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
                autoComplete="new-password"
                placeholder="Repita la contraseña"
                value={confirmacion}
                onChange={(e) => setConfirmacion(e.target.value)}
              />
            </div>

            {error && <p role="alert">{error}</p>}

            <div className="divisorx">
              <button
                type="button"
                className="rojo"
                onClick={() => {
                  confirmar(
                    "Si salís ahora, tendrás que cambiar tu contraseña la próxima vez que ingreses. ¿Querés continuar?",
                    () => navigate("/home", { replace: true })
                  );
                }}
              >
                Mantener
              </button>

              <button
                type="button"
                className="azul"
                onClick={handleCambiar}
              >
                Cambiar
              </button>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

export default Camcontra;
