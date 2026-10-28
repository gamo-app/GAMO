
import { createRoot } from "react-dom/client";
import Icon from "../components/Icon";

export function confirmar(
  mensaje: string,
  accion: () => void | Promise<void>
): void {
  const contenedor = document.createElement("div");
  document.body.appendChild(contenedor);

  const root = createRoot(contenedor);
  let cerrada = false;

  function cerrar() {
    if (cerrada) return;
    cerrada = true;

    root.unmount();
    contenedor.remove();
  }

  function Alerta() {
    return (
      <div className="alerta-fondo">
        <div className="alerta">
          <Icon tipo={23} tamaño={15} />

          <h3 className="centro">¿Estás seguro?</h3>
          <p className="centro">{mensaje}</p>

          <div className="divisorx">
            <button className="rojo" onClick={cerrar}>
              No
            </button>

            <button
              className="azul"
              onClick={() => {
                cerrar();
                void accion();
              }}
            >
              Sí, continuar
            </button>
          </div>
        </div>
      </div>
    );
  }

  root.render(<Alerta />);
}
