import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { confirmar } from "../utils/confirmar";
import { evaluarMembresia, type SocioListado } from "../api/Socios";
import { useAuth } from "../context/AuthContext";
import { storage } from "../storage/Storage";

type Props = {
  socio?: SocioListado;
};

function Perfil({ socio }: Props) {
  const navigate = useNavigate();
  const { id } = useParams();
  const { usuario, logout } = useAuth();

  const esMiUsuario = !id && !socio;

  const [modoOscuro, setModoOscuro] = useState(
    storage.get<boolean>("modoOscuro") ?? false
  );
  const [error, setError] = useState("");

  const { estado, membresia } = socio
    ? evaluarMembresia(socio.membresias)
    : { estado: "", membresia: undefined };

  const nombre = socio?.usuario
    ? `${socio.usuario.nombre} ${socio.usuario.apellido}`
    : esMiUsuario && usuario
      ? `${usuario.nombre} ${usuario.apellido}`
      : "Usuario no disponible";

  function cambiarModo(event: React.ChangeEvent<HTMLSelectElement>) {
    const nuevoModo = event.target.value === "true";
    setModoOscuro(nuevoModo);
    storage.set("modoOscuro", nuevoModo); // o false
  window.dispatchEvent(new Event("modoOscuroCambiado"));
  }

  async function handleCerrarSesion() {
    setError("");

    try {
      await logout();
      navigate("/", { replace: true });
    } catch (error: unknown) {
      console.error("Error al cerrar sesión:", error);
      setError(
        error instanceof Error
          ? error.message
          : "No se pudo cerrar la sesión en el servidor."
      );
    }
  }

  return (
    <section>
      <div className="listabloques">
        <div className={esMiUsuario ? "bloque" : "bloque4"}>
          <div className="cuadrado2 iconoestado4">
            <span aria-hidden="true">
              {nombre.slice(0, 1).toLocaleUpperCase()}
            </span>
          </div>

          <h2>{nombre}</h2>

          {esMiUsuario ? (
            
            <>
                                                            {/*MOSTRAR USUARIO ACTUAL*/}
              <p>{usuario?.email ?? "-"}</p>

              <label htmlFor="modo-oscuro">Apariencia</label>
              <select
                id="modo-oscuro"
                className="blanco"
                value={String(modoOscuro)}
                onChange={cambiarModo}
              >
                <option value="false">Modo claro</option>
                <option value="true">Modo oscuro</option>
              </select>

              {error && <p role="alert">{error}</p>}

          <button
            type="button"
            className="rojo"
            onClick={() => {
              confirmar(
                "¿Estás seguro de que querés cerrar sesión?",
                () => void handleCerrarSesion()
              );
            }}
          >
            Cerrar sesión
          </button>
            </>
          ) : socio ? (
            <>
                                                            {/*MOSTRAR UN SOCIO O PERFIL DE UN TERCERO*/}
              <p>Credencial: {socio.codigo_credencial}</p>

              <div className="listay2">
                <label>DNI</label>
                <div className="finput">
                  {socio.usuario?.DNI ?? "-"}
                </div>

                <label>Fecha de nacimiento</label>
                <div className="finput">
                  {socio.usuario?.fecha_nacimiento ?? "-"}
                </div>

                <label>Estado de membresía</label>
                <div className="finput">
                  {estado.replace("_", " ")}
                </div>

                <label>Plan</label>
                <div className="finput">
                  {membresia?.plan?.nombre ?? "Sin membresía"}
                </div>

                <label>Inicio de membresía</label>
                <div className="finput">
                  {membresia?.fecha_inicio ?? "-"}
                </div>

                <label>Fin de membresía</label>
                <div className="finput">
                  {membresia?.fecha_fin ?? "-"}
                </div>
              </div>

              <Link to="/gestion" className="azul2">
                Volver a socios
              </Link>
            </>
          ) : (
            <p>No se encontraron los datos del usuario.</p>
          )}
        </div>
      </div>
    </section>
  );
}

export default Perfil;