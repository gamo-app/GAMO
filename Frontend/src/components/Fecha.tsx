import { useState } from "react";

function Fecha() {
  const [dia, setDia] = useState("");
  const [mes, setMes] = useState("");
  const [año, setAño] = useState("");

  const meses = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
  ];

  // Cantidad de días según mes y año
  const cantidadDias =
    mes && año ? new Date(Number(año), Number(mes), 0).getDate() : 31;

  const años = Array.from(
    { length: 100 },
    (_, i) => new Date().getFullYear() - i
  );

  const dias = Array.from({ length: cantidadDias }, (_, i) => i + 1);

  return (
    <>
      <label htmlFor="fecha">Fecha de nacimiento</label>

      <div className="inputfecha">
        {/* Día */}
        <select
          id="dia"
          name="dia"
          value={dia}
          onChange={(e) => setDia(e.target.value)}
        >
          <option value="">Día</option>

          {dias.map((dia) => (
            <option key={dia} value={dia}>
              {dia}
            </option>
          ))}
        </select>

        <p>/</p>

        {/* Mes */}
        <select
          id="mes"
          name="mes"
          value={mes}
          onChange={(e) => {
            setMes(e.target.value);

            // Si el día seleccionado ya no existe en el nuevo mes
            const nuevosDias = new Date(
              Number(año) || 2000,
              Number(e.target.value),
              0
            ).getDate();

            if (Number(dia) > nuevosDias) {
              setDia("");
            }
          }}
        >
          <option value="">Mes</option>

          {meses.map((mes, index) => (
            <option key={mes} value={index + 1}>
              {mes}
            </option>
          ))}
        </select>

        <p>/</p>

        {/* Año */}
        <select
          id="año"
          name="año"
          value={año}
          onChange={(e) => {
            setAño(e.target.value);

            // Controlar el 29 de febrero en años no bisiestos
            if (dia && mes) {
              const nuevosDias = new Date(
                Number(e.target.value),
                Number(mes),
                0
              ).getDate();

              if (Number(dia) > nuevosDias) {
                setDia("");
              }
            }
          }}
        >
          <option value="">Año</option>

          {años.map((año) => (
            <option key={año} value={año}>
              {año}
            </option>
          ))}
        </select>
      </div>
    </>
  );
}

export default Fecha;