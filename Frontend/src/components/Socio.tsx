
import Icon from "./Icon";
import { Link } from "react-router-dom";
import type { SocioData } from "../database/Api";

type SocioProps = {
  socio?: SocioData;
  carga?: boolean;
  inasistencias?: number;
  sede?: string;

};

function Socio({
  socio,
  carga = false,
  inasistencias = 0,
  sede,

}: SocioProps) {
  const nombre = socio
    ? `${socio.nombre ?? ""} ${socio.apellido ?? ""}`.trim()
    : "";

  const nombreSede =
    sede ??
    socio?.sede ??
    (socio?.id_sede ? `Sede ${socio.id_sede}` : "Sin sede");

  const esMoroso =
    socio?.estado_cuota === "vencida" || inasistencias >= 10;

  return (
    <article
      className={`rectangulo ${esMoroso ? "borderojo" : ""} ${
        carga ? "cargando" : ""
      }`}
    >
      <div className="divisorx">
        <div
          className={`cuadrado ${
            esMoroso
              ? "iconoestado2"
              : socio?.estado_cuota === "pagada"
              ? "iconoestado1"
              : socio?.estado_cuota === "pendiente"
              ? "iconoestado0"
              : "iconoestado4"
          } iconoperfil`}
        >
          <Icon
            tipo={2}
            color={esMoroso ? 4 : 0}
            tamaño={3.6}
          />
        </div>

        <div className="texto2">
          <h4>
            {socio ? (
              <Link
                to={`/gestion/${socio.id_socio}`}
                style={{ color: "inherit", textDecoration: "none" }}
              >
                {nombre || "Sin nombre"}
              </Link>
            ) : (
              "Sin nombre"
            )}
          </h4>

          <div className="divisorx3">
            <Icon tipo={14} color={0} tamaño={1.3} />
            <p>{nombreSede}</p>
          </div>
        </div>
      </div>

      {socio && (
        <Link
          className="botoncuadrado"
          to={`/gestion/${socio.id_socio}`}
          aria-label={`Ver detalles de ${nombre}`}
        >
          <Icon tipo={13} tamaño={3} />
        </Link>
      )}
    </article>
  );
}

export default Socio;
