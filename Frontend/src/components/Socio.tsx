import { Link } from "react-router-dom";

import Icon from "./Icon";
import { evaluarMembresia, type SocioListado } from "../database/Socios";

type SocioProps = {
  socio?: SocioListado;
  carga?: boolean;
};

function Socio({ socio, carga = false }: SocioProps) {
  const nombre = socio?.usuario
    ? `${socio.usuario.nombre} ${socio.usuario.apellido}`
    : "Usuario no disponible";
  const { estado, membresia } = socio
    ? evaluarMembresia(socio.membresias)
    : { estado: null, membresia: null };

  const estadoClase = {
    activo: "iconoestado1",
    pendiente: "iconoestado0",
    inactivo: "iconoestado2",
    sin_membresia: "iconoestado4",
  }[estado ?? "sin_membresia"];

  return (
    <article
      className={`rectangulo ${
        estado === "inactivo" ? "borderojo" : ""
      } ${carga ? "cargando" : ""}`}
    >
      <div className="divisorx">
        <div className={`cuadrado ${estadoClase} iconoperfil`}>
          <Icon
            tipo={2}
            color={estado === "inactivo" ? 4 : 0}
            tamaño={3.6}
          />
        </div>

        <div className="texto2">
          <h4>
            {socio ? (
              <Link
                to={`/socios/${socio.codigo_credencial}`}
                style={{ color: "inherit" }}
              >
                {nombre}
              </Link>
            ) : (
              nombre
            )}
          </h4>
          <div className="divisorx3">
            <p>{membresia?.plan?.nombre ?? "Sin membresía"}</p>
            <p aria-hidden="true">·</p>
            <p>{estado?.replace("_", " ") ?? "Sin membresía"}</p>
          </div>
        </div>
      </div>

      {socio && (
        <Link
          className="botoncuadrado"
          to={`/socios/${socio.codigo_credencial}`}
          aria-label={`Ver detalles de ${nombre}`}
        >
          <Icon tipo={13} tamaño={3} />
        </Link>
      )}
    </article>
  );
}

export default Socio;
