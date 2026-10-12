import { useEffect, useState } from "react";
import { Html5Qrcode } from "html5-qrcode";
import Header from "../components/Header";
import Main from "../components/Main";
function Escanear() {
  
  const [codigo, setCodigo] = useState("");

  useEffect(() => {
    const scanner = new Html5Qrcode("lector-qr");

    let iniciado = false;

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
              scanner
                .stop()
                .then(() => {
                  iniciado = false;
                })
                .catch(() => {});
            }
          },
          () => {}
        );

        iniciado = true;
      } catch (error) {
        console.error("No se pudo iniciar la cámara:", error);
      }
    };

    iniciarScanner();

    return () => {
      if (iniciado) {
        scanner.stop().catch(() => {});
      }
    };
  }, []);

  return (
    <Main>
  <Header></Header>

<section className="escanear">
 
      
      <div className="texto-escanear">
        
      </div>

      {/* Cámara */}
      <div
        id="lector-qr"
        className="lector-qr"
      />

      {/* Código detectado */}
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