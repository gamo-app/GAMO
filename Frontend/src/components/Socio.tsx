import Icon from "./Icon";
import { Link } from "react-router-dom";
import type { SocioData } from "../database/Api";

type SocioProps = {
  socio?: SocioData;
  carga?: boolean;
  inasistencias?: number;
  sede?: string;
  onCambiarEstado?: (socio: SocioData) => void;
};

function Socio({
  socio,
  carga = false,
  inasistencias = 0,
  sede,
  onCambiarEstado,
}: SocioProps) {
  const nombre = socio
    ? `${socio.nombre ?? ""} ${socio.apellido ?? ""}`.trim()
    : "";

  const nombreSede =
    sede ??
    socio?.sede ??
    (socio?.id_sede ? `Sede ${socio.id_sede}` : "Sin sede");

  const telefonoLimpio = (socio?.telefono ?? "").replace(/\D/g, "");
  const telefonoWhatsApp = telefonoLimpio.replace(/^54/, "");

  const esMoroso =
    socio?.estado_cuota === "vencida" || inasistencias >= 10;

  return (
    <article
      className={`rectangulo ${esMoroso ? "borderojo" : ""} ${
        carga ? "cargando" : ""
      }`}
    >
      <div className="divisorx">
        {/* Icono de perfil con color según estado de cuota */}
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

        {/* Nombre y credencial/sede */}
        <div className="texto2">
          <h4>
            {socio ? (
              <Link
                to={`/socios/${socio.id_socio}`}
                style={{ color: "inherit", textDecoration: "none" }}
              >
                {nombre || "Sin nombre"}
              </Link>
            ) : (
              "Sin nombre"
            )}
          </h4>

          <div className="divisorx2">
            <Icon tipo={14} color={0} tamaño={1.3} />
            <p>{nombreSede}</p>
          </div>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Fecha de alta</h4>
          <p>{socio?.fecha_alta ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>DNI</h4>
          <p>{socio?.dni ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Teléfono</h4>
          <p>{socio?.telefono ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Plan</h4>
          <p>{socio?.plan ?? "Sin plan"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Estado</h4>
          <p>{socio?.estado ?? "-"}</p>
        </div>

        <div className="barra pc" />

        <div className="texto2 pc">
          <h4>Cuota</h4>
          <p>{socio?.estado_cuota ?? "sin_cuota"}</p>
        </div>
      </div>

      {/* Acciones para PC */}
      {socio && (
        <div className="divisorx pc">
          <div className="barra"></div>

          {socio.email && (
            <a
              href={`mailto:${socio.email}`}
              className="circuloazul"
              aria-label={`Enviar correo a ${nombre}`}
            >
              <Icon tipo={15} tamaño={2} />
            </a>
          )}

          {telefonoLimpio && (
            <a
              href={`tel:${telefonoLimpio}`}
              className="circuloazul"
              aria-label={`Llamar a ${nombre}`}
            >
              <Icon tipo={17} tamaño={2} />
            </a>
          )}

          {telefonoWhatsApp && (
            <a
              href={`https://wa.me/54${telefonoWhatsApp}`}
              className="circuloazul"
              target="_blank"
              rel="noreferrer"
              aria-label={`Contactar por WhatsApp a ${nombre}`}
            >
              <Icon tipo={16} tamaño={2} />
            </a>
          )}

          <div className="barra"></div>

          <a
            className="circulorojo"
            onClick={() => onCambiarEstado && onCambiarEstado(socio)}
            title={
              socio.estado === "inactivo"
                ? "Reactivar socio"
                : "Dar de baja socio"
            }
          >
            <Icon tipo={20} tamaño={2} />
          </a>
        </div>
      )}

      {/* Acceso al detalle en móvil */}
      {socio && (
        <Link
          className="botoncuadrado mobile"
          to={`/socios/${socio.id_socio}`}
        >
          <Icon tipo={13} tamaño={3} />
        </Link>
      )}
    </article>
  );
}

export default Socio;