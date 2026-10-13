import { useState } from "react";
import {  useNavigate } from "react-router-dom";
import Header from "../components/Header";
import Fecha from "../components/Fecha";
import Main from "../components/Main";
function Sign() {
  
  const [paso, setPaso] = useState(1);
  const navigate = useNavigate();

  const siguiente = () => {
    setPaso(2);
  };

  const anterior = () => {
    setPaso(1);
  };

  const cancelar = () => {
    navigate("/");
  };

  const crearCuenta = () => {
    // Acá después podés agregar la lógica
    // para registrar el usuario.

    navigate("/");
  };

  return (
    <Main>
      <Header />

      <section className="login">
        <form className="listabloques">

          {/* PASO 1 */}
          {paso === 1 && (
            <div className="bloque espaciado">
<div className="input">
  <label htmlFor="nombre">Nombre</label>
              <input
                id="nombre"
                className="blanco"
                type="text"
                placeholder="Luciano"
              />
</div>
            
<div className="input">
<label htmlFor="apellido">Apellido</label>
              <input
                id="apellido"
                className="blanco"
                type="text"
                placeholder="Barbini"
              />
</div>
              
<div className="input">
  <label htmlFor="dni">DNI</label>
              <input
                id="dni"
                className="blanco"
                type="number"
                placeholder="--------"
              />
</div>
              

              <Fecha></Fecha>
              
<div className="divisorx">
   <button
                type="button"
                className="blanco"
                onClick={cancelar}
              >
                Cancelar
              </button>
<button
                type="button"
                className="azul"
                onClick={siguiente}
              >
                Siguiente
              </button>

             
</div>
              
            </div>
          )}

          {/* PASO 2 */}
          {paso === 2 && (
            <div className="bloque espaciado">
<div className="input">
 <label htmlFor="telefono">Teléfono</label>
              <input
                id="telefono"
                className="blanco"
                type="tel"
                placeholder="11 ---- ----"
              />
</div>
             
<div className="input">
   <label htmlFor="correo">Correo</label>
              <input
                id="correo"
                className="blanco"
                type="email"
                placeholder="correo@mail.com"
              />
</div>
             
<div className="input">
  <label htmlFor="password">Contraseña</label>
              <input
                id="password"
                className="blanco"
                type="password"
                placeholder="-----"
              />
</div>
              
<div className="input">
   <label htmlFor="confirmarPassword">
                Confirmar contraseña
              </label>

              <input
                id="confirmarPassword"
                className="blanco"
                type="password"
                placeholder="-----"
              />
</div>

<div className="divisorx">
             


              <button
                type="button"
                className="blanco"
                onClick={anterior}
              >
                Atrás
              </button>
               <button
                type="button"
                className="azul"
                onClick={crearCuenta}
              >
                Crear cuenta
              </button>
</div>
             

             
            </div>
          )}

         

        </form>
      </section>
  </Main>
  );
}

export default Sign;