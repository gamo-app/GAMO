
import { createRoot } from "react-dom/client";
import Icon from "../components/Icon";
type TipoAlerta = "info" | "error" | "exito";

export function alerta(
  mensaje: string,
  tipo: TipoAlerta = "info"
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

  const titulos: Record<TipoAlerta, string> = {
    info: "Aviso",
    error: "Ocurrió un error",
    exito: "Operación exitosa",
  };

  root.render(
    <div className="alerta-fondo">
         <Icon tipo={25} tamaño={15} ></Icon>
      <div className="alerta">
        <h3 className="centro">{titulos[tipo]}</h3>
        <p className="centro">{mensaje}</p>

        <div className="divisorx">
          <button className="azul" onClick={cerrar}>
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}
