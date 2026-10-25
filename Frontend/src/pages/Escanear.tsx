import { useEffect, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import Header from "../components/Header";
import Main from "../components/Main";
import Icon from "../components/Icon";

function Escanear() {
  const [codigo, setCodigo] = useState("");
  const [errorCamara, setErrorCamara] = useState(false);

  useEffect(() => {
    const scanner = new Html5Qrcode("lector-qr");
    let iniciado = false;
    let cancelado = false;

    const iniciarScanner = async () => {
      try {
        await scanner.start(
          { facingMode: "environment" },
          {
            fps: 10,
            qrbox: {
              width: 250,
              height: 250,
            },
          },
          (texto) => {
            setCodigo(texto);

            if (iniciado) {
              scanner.stop().then(() => {
                iniciado = false;
              }).catch(() => {});
            }
          },
          () => {}
        );

        iniciado = true;

        if (cancelado) {
          await scanner.stop().catch(() => {});
          iniciado = false;
        }
      } catch (error) {
        console.error("No se pudo iniciar la cámara:", error);

        if (!cancelado) {
          setErrorCamara(true);
        }
      }
    };

    iniciarScanner();

    return () => {
      cancelado = true;

      if (iniciado) {
        scanner.stop().catch(() => {});
      }
    };
  }, []);

  return (
    <Main>
      <Header atras />

      <section className={errorCamara ? "escanear centro" :"escanear"}>
        <div className="texto-escanear"></div>

        {errorCamara ? (
          <>
            <Icon tipo={12} tamaño={10} />
            <p>No se pudo conectar a la cámara.</p>
            <p>Verificá los permisos de cámara e intentá nuevamente.</p>
          </>
        ) : (
          <div id="lector-qr" className="lector-qr" />
        )}

        {codigo && (
          <div className="codigo">
            <p>Código:</p>
            <strong>{codigo}</strong>
          </div>
        )}
      </section>
    </Main>
  );
}

export default Escanear;