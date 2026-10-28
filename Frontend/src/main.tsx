
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import RutaProtegida from "./components/RutaProtegida";
import Layout from "./components/Layout";

import "./assets/css/animations.css";
import "./assets/css/index.css";
import "./assets/css/responsive.css";

import Agregarsocio from "./pages/Agregarsocio";
import Camcontra from "./pages/Camcontra";
import Error from "./pages/404";
import Escanear from "./pages/Escanear";
import Gestion from "./pages/Gestion";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Sign from "./pages/Sign";
import Perfil from "./pages/Perfil";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            {/* Páginas públicas */}
            <Route path="/" element={<Login />} />
            <Route path="/crear" element={<Sign />} />

            {/* Cualquier usuario con sesión iniciada */}
            <Route element={<RutaProtegida />}>
              <Route path="/home" element={<Home />} />
              <Route path="/notificacion" element={<Home />} />
              <Route path="/buscar" element={<Home />} />
              <Route path="/perfil" element={<Perfil />} />
              <Route
                path="/contraseña"
                element={<Camcontra />}
              />

          
                <Route path="/horarios" element={<Home />} />
         

              <Route
                element={
                  <RutaProtegida permiso="administrar_socios" />
                }
              >
                <Route path="/gestion" element={<Gestion />} />
                <Route
                  path="/perfil/:id"
                  element={<Gestion />}
                />
                <Route
                  path="/agregarsocio"
                  element={<Agregarsocio />}
                />
                <Route
                  path="/agregar/:tipo"
                  element={<Agregarsocio />}
                />
              </Route>

           
                <Route
                  path="/escanear"
                  element={<Escanear />}
                />
                <Route path="/escanear/:id" element={<Escanear />} />
      
            </Route>
          </Route>

          {/* Página no encontrada */}
          <Route path="*" element={<Error />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
