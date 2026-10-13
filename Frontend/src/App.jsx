import { useState } from "react";
import Recepcion from "./recepcion";
import Admin from "./admin";
import "./App.css";

function App() {
  const [vista, setVista] = useState("recepcion"); // 'recepcion' o 'admin'

  return (
    <main style={{ padding: "20px", fontFamily: "sans-serif" }}>
      <header style={{ textAlign: "center", marginBottom: "20px" }}>
        <h1>Sistema de Gestión de Club</h1>

        {/* Botones para alternar entre pantallas */}
        <div style={{ marginTop: "10px" }}>
          <button
            onClick={() => setVista("recepcion")}
            style={{
              padding: "8px 16px",
              marginRight: "10px",
              background: vista === "recepcion" ? "#007bff" : "#e0e0e0",
              color: vista === "recepcion" ? "white" : "black",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Vista Recepción
          </button>

          <button
            onClick={() => setVista("admin")}
            style={{
              padding: "8px 16px",
              background: vista === "admin" ? "#28a745" : "#e0e0e0",
              color: vista === "admin" ? "white" : "black",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Vista Administrador
          </button>
        </div>
      </header>

      {/* Renderizado condicional según la pestaña activa */}
      {vista === "recepcion" ? <Recepcion /> : <Admin />}
    </main>
  );
}

export default App;