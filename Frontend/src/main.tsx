import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import RutaProtegida from "./components/RutaProtegida";
import { AuthProvider } from "./context/AuthContext";
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
import Layout from "./components/Layout"
import Sign from "./pages/Sign";
import Perfil from "./pages/Perfil";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
            <Route element={<Layout />}>

          <Route path="/" element={<Login />} />
          <Route path="/crear" element={<Sign />} />

          <Route element={<RutaProtegida />}>
              <Route path="/home" element={<Home />} />
              <Route path="/notificacion" element={<Home />} />
              <Route path="/horarios" element={<Home />} />
              <Route path="/buscar" element={<Home />} />
              <Route path="/gestion" element={<Gestion />} />
              <Route path="/gestion/:id" element={<Gestion />} />
              <Route path="/agregarsocio" element={<Agregarsocio />} />
              <Route path="/agregar/:tipo" element={<Agregarsocio />} />
              <Route path="/perfil" element={<Perfil />} />
              <Route path="/escanear" element={<Escanear />} />
              <Route path="/contraseña" element={<Camcontra />} />
          </Route>
          </Route>

          <Route path="*" element={<Error />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
