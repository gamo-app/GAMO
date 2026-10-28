
import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Html5Qrcode } from "html5-qrcode";
import { QRCodeSVG } from "qrcode.react";

import { registrarAsistencia } from "../api/Api";
import Icon from "../components/Icon";
import { useAuth } from "../context/AuthContext";
import { alerta } from "../utils/alerta";

function Escanear() {
  const { usuario, cargando } = useAuth();
  const { id } = useParams<{ id: string }>();

  const [escaneando, setEscaneando] = useState(false);
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const procesandoRef = useRef(false);
  const idsProcesadosRef = useRef(new Set<string>());

  function obtenerId(texto: string): string {
    const valor = texto.trim();

    try {
      const url = new URL(valor);
      const partes = url.pathname.split("/").filter(Boolean);

      const indiceEscanear = partes.lastIndexOf("escanear");
      if (indiceEscanear !== -1 && partes[indiceEscanear + 1]) {
        return decodeURIComponent(partes[indiceEscanear + 1]);
      }

      const indicePerfil = partes.lastIndexOf("perfil");
      if (indicePerfil !== -1 && partes[indicePerfil + 1]) {
        return decodeURIComponent(partes[indicePerfil + 1]);
      }

      return decodeURIComponent(partes[partes.length - 1] || "");
    } catch {
      return valor;
    }
  }

  async function procesarAsistencia(idUsuario: string) {
    if (!idUsuario || procesandoRef.current) return;
    if (idsProcesadosRef.current.has(idUsuario)) return;

    procesandoRef.current = true;
    idsProcesadosRef.current.add(idUsuario);
    setEscaneando(false);

    try {
      const exitoso = await registrarAsistencia(idUsuario);

      if (!exitoso) {
        idsProcesadosRef.current.delete(idUsuario);
      }
    } finally {
      procesandoRef.current = false;
    }
  }

  async function procesarQR(texto: string) {
    const idLeido = obtenerId(texto);

    if (!idLeido) {
      alerta("No se pudo obtener el ID del usuario.", "error");
      return;
    }

    await procesarAsistencia(idLeido);
  }

  // Si la URL es /escanear/12123242, registra ese ID al entrar.
  useEffect(() => {
    if (!id) return;

    void procesarAsistencia(id);
  }, [id]);

  useEffect(() => {
    if (!escaneando) return;

    let cancelado = false;
    let iniciado = false;
    let procesado = false;

    const scanner = new Html5Qrcode("lector-qr");
    scannerRef.current = scanner;

    async function iniciarScanner() {
      try {
        await scanner.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: { width: 250, height: 250 } },
          async (texto) => {
            if (cancelado || procesado) return;

            procesado = true;

            try {
              await scanner.stop();
              iniciado = false;
              scanner.clear();
            } catch {
              // La cámara ya puede estar detenida.
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

      scannerRef.current = null;
    };
  }, [escaneando]);

  function iniciarEscaneo() {
    setEscaneando(true);
  }

  if (cargando) {
    return (
      <section className="escanear centro">
        <p>Cargando credencial...</p>
      </section>
    );
  }

  const idUsuario = usuario?.uuid_usuario;

  return (
    <section className={`escanear ${escaneando ? "modo-escaneo" : ""}`}>
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
        <div className="listabloques">
          <div className="bloque">
            <h2>Mi credencial</h2>
            <p>Mostrá este código para identificar tu usuario.</p>

            {idUsuario ? (
              <div className="qr-usuario">
                <QRCodeSVG
                  className="qr"
                  value={`${window.location.origin}/escanear/${encodeURIComponent(idUsuario)}`}
                  size={220}
                  level="L"
                  marginSize={2}
                />
              </div>
            ) : (
              <>
                <Icon tipo={12} tamaño={5} />
                <p>No se pudo obtener el ID del usuario.</p>
              </>
            )}

            <h2>Escanear QR</h2>
            <p>Activá la cámara para leer una credencial.</p>

            <button
              type="button"
              className="azul"
              onClick={iniciarEscaneo}
              disabled={procesandoRef.current}
            >
              Escanear QR
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export default Escanear;
