
import { useCallback, useEffect, useRef, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import { QRCodeSVG } from "qrcode.react";

import {
  obtenerClasesAsistencia,
  obtenerMisAsistencias,
  obtenerQrSede,
  obtenerSedesAsistencia,
  registrarAsistencia,
  registrarAsistenciaQr,
} from "../api/Api";
import type {
  AsistenciaListado,
  ClaseAsistencia,
  SedeAsistencia,
} from "../api/Socios";
import { useAuth } from "../context/AuthContext";
import { alerta } from "../utils/alerta";

function Escanear() {
  const { usuario, cargando } = useAuth();
  const rol = usuario?.rol?.nombre?.trim().toLowerCase() ?? "";
  const esSocio = rol === "socio";
  const puedeRegistrar = ["admin", "profesor", "representante"].includes(rol);
  const puedeGenerarQr = ["admin", "profesor"].includes(rol);

  const [clases, setClases] = useState<ClaseAsistencia[]>([]);
  const [sedes, setSedes] = useState<SedeAsistencia[]>([]);
  const [asistencias, setAsistencias] = useState<AsistenciaListado[]>([]);
  const [cargandoDatos, setCargandoDatos] = useState(true);
  const [errorCarga, setErrorCarga] = useState("");
  const [escaneando, setEscaneando] = useState(false);
  const [procesando, setProcesando] = useState(false);
  const [idSede, setIdSede] = useState("");
  const [qrPayload, setQrPayload] = useState("");
  const [uuidClase, setUuidClase] = useState("");
  const [codigoCredencial, setCodigoCredencial] = useState("");
  const [fecha, setFecha] = useState(fechaLocalActual);
  const procesandoRef = useRef(false);

  useEffect(() => {
    let activo = true;
    const tareas: Promise<void>[] = [];

    if (esSocio) {
      tareas.push(
        obtenerMisAsistencias()
          .then((resultado) => {
            if (activo) setAsistencias(resultado);
          })
          .catch((error: unknown) => {
            console.error("No se pudieron cargar las asistencias:", error);
            if (activo) setErrorCarga("No se pudo cargar tu historial.");
          })
      );
    }

    if (puedeRegistrar) {
      tareas.push(
        obtenerClasesAsistencia()
          .then((resultado) => {
            if (activo) setClases(resultado);
          })
          .catch((error: unknown) => {
            console.error("No se pudieron cargar las clases:", error);
            if (activo) setErrorCarga("No se pudieron cargar las clases.");
          })
          .finally(() => {
            if (activo) setCargandoDatos(false);
          })
      );
    }

    if (puedeGenerarQr) {
      tareas.push(
        obtenerSedesAsistencia()
          .then((resultado) => {
            if (activo) setSedes(resultado);
          })
          .catch((error: unknown) => {
            console.error("No se pudieron cargar las sedes:", error);
            if (activo) setErrorCarga("No se pudieron cargar las sedes.");
          })
      );
    }

    void Promise.all(tareas);
    return () => {
      activo = false;
    };
  }, [esSocio, puedeGenerarQr, puedeRegistrar]);

  const procesarQR = useCallback(async (texto: string) => {
    const qrLeido = texto.trim();
    if (!esSocio || !qrLeido || procesandoRef.current) return;

    procesandoRef.current = true;
    setProcesando(true);
    setEscaneando(false);

    try {
      try {
        await registrarAsistenciaQr(qrLeido);
      } catch (error: unknown) {
        console.error("No se pudo registrar la asistencia por QR:", error);
        return;
      }

      try {
        const resultado = await obtenerMisAsistencias();
        setAsistencias(resultado);
      } catch (error: unknown) {
        console.error("No se pudo actualizar el historial:", error);
        setErrorCarga(
          "La asistencia se registró, pero no se pudo actualizar el historial."
        );
      }
    } finally {
      procesandoRef.current = false;
      setProcesando(false);
    }
  }, [esSocio]);

  useEffect(() => {
    if (!escaneando || !esSocio) return;

    let cancelado = false;
    let iniciado = false;
    let procesado = false;
    const scanner = new Html5Qrcode("lector-qr");

    async function iniciarScanner() {
      try {
        await scanner.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: { width: 250, height: 250 } },
          async (texto) => {
            if (cancelado || procesado) return;

            procesado = true;
            setEscaneando(false);

            try {
              await scanner.stop();
              iniciado = false;
              scanner.clear();
            } catch {
              // La cámara puede haberse detenido al desmontar el lector.
            }

            if (!cancelado) {
              await procesarQR(texto);
            }
          },
          () => {}
        );

        iniciado = true;

        if (cancelado) {
          await scanner.stop().catch(() => {});
          iniciado = false;
          scanner.clear();
        }
      } catch (error) {
        if (!cancelado) {
          console.error("No se pudo iniciar la cámara:", error);
          setEscaneando(false);
          alerta(
            "No se pudo conectar a la cámara. Verificá los permisos e intentá nuevamente.",
            "error"
          );
        }
      }
    }

    void iniciarScanner();

    return () => {
      cancelado = true;

      if (iniciado) {
        void scanner.stop().catch(() => {}).finally(() => scanner.clear());
      }
    };
  }, [escaneando, esSocio, procesarQR]);

  async function generarQr() {
    if (!idSede) return;

    setErrorCarga("");
    try {
      const resultado = await obtenerQrSede(Number(idSede));
      setQrPayload(resultado.qr_payload);
    } catch (error: unknown) {
      console.error("No se pudo generar el QR de la sede:", error);
      setQrPayload("");
      setErrorCarga("No se pudo generar el QR de la sede.");
    }
  }

  async function enviarAsistencia(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorCarga("");

    try {
      await registrarAsistencia({
        uuid_clase: uuidClase,
        fecha,
        codigo_credencial: codigoCredencial.trim(),
      });
      setCodigoCredencial("");
    } catch (error: unknown) {
      console.error("No se pudo registrar la asistencia manual:", error);
    }
  }

  if (cargando) {
    return (
      <section className="escanear centro">
        <p>Verificando sesión...</p>
      </section>
    );
  }

  return (
    <section className={`escanear ${escaneando ? "modo-escaneo" : ""}`}>
      {esSocio ? (
        <div className="listabloques">
          <div className="bloque">
            <h2>Registrar asistencia</h2>
            <p>Escaneá el QR de tu sede para registrar la clase activa.</p>

            {escaneando ? (
              <div className="lector-pantalla">
                <div id="lector-qr" className="lector-qr" />
                <button
                  type="button"
                  className="azul"
                  onClick={() => setEscaneando(false)}
                >
                  Cancelar escaneo
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="azul"
                onClick={() => setEscaneando(true)}
                disabled={procesando}
              >
                Escanear QR de sede
              </button>
            )}

            <h3>Mis asistencias</h3>
            {asistencias.length === 0 ? (
              <p>Todavía no tenés asistencias registradas.</p>
            ) : (
              <ul>
                {asistencias.map((asistencia) => (
                  <li key={asistencia.id_asistencia}>
                    {asistencia.fecha} · Clase {asistencia.uuid_clase}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : puedeRegistrar ? (
        <div className="listabloques">
          {puedeGenerarQr && (
            <div className="bloque">
              <h2>QR de asistencia por sede</h2>
              <p>Generá el QR que los socios deben escanear en la sede.</p>
              <label htmlFor="sede-qr">Sede</label>
              <select
                id="sede-qr"
                className="blanco"
                value={idSede}
                onChange={(event) => {
                  setIdSede(event.target.value);
                  setQrPayload("");
                }}
                disabled={sedes.length === 0}
              >
                <option value="">Seleccioná una sede</option>
                {sedes.map((sede) => (
                  <option key={sede.id_sede} value={sede.id_sede}>
                    {sede.nombre}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="azul"
                onClick={() => void generarQr()}
                disabled={!idSede}
              >
                Mostrar QR
              </button>
              {qrPayload && (
                <div className="qr-usuario">
                  <QRCodeSVG
                    className="qr"
                    value={qrPayload}
                    size={220}
                    level="M"
                    marginSize={2}
                  />
                </div>
              )}
            </div>
          )}

          <form className="bloque" onSubmit={enviarAsistencia}>
            <h2>Registrar asistencia manual</h2>
            <label htmlFor="clase-asistencia">Clase</label>
            <select
              id="clase-asistencia"
              className="blanco"
              value={uuidClase}
              onChange={(event) => setUuidClase(event.target.value)}
              required
              disabled={cargandoDatos || clases.length === 0}
            >
              <option value="">Seleccioná una clase</option>
              {clases.map((clase) => (
                <option key={clase.uuid_clase} value={clase.uuid_clase}>
                  {clase.dia_de_semana} · {clase.hora_inicio}–{clase.hora_fin}
                </option>
              ))}
            </select>

            <label htmlFor="credencial-asistencia">Código de credencial</label>
            <input
              id="credencial-asistencia"
              className="blanco"
              type="text"
              value={codigoCredencial}
              onChange={(event) => setCodigoCredencial(event.target.value)}
              required
            />

            <label htmlFor="fecha-asistencia">Fecha</label>
            <input
              id="fecha-asistencia"
              className="blanco"
              type="date"
              value={fecha}
              onChange={(event) => setFecha(event.target.value)}
              required
            />

            <button
              type="submit"
              className="azul"
              disabled={cargandoDatos || clases.length === 0}
            >
              Registrar asistencia
            </button>
          </form>
        </div>
      ) : (
        <div className="listabloques">
          <div className="bloque">
            <h2>Asistencias</h2>
            <p>Tu rol no tiene acceso a estas funciones.</p>
          </div>
        </div>
      )}
      {errorCarga && <p role="alert">{errorCarga}</p>}
    </section>
  );
}

function fechaLocalActual(): string {
  const hoy = new Date();
  const año = hoy.getFullYear();
  const mes = String(hoy.getMonth() + 1).padStart(2, "0");
  const dia = String(hoy.getDate()).padStart(2, "0");
  return `${año}-${mes}-${dia}`;
}

export default Escanear;
