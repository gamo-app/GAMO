import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import RutaProtegida from "./components/RutaProtegida";
import { AuthProvider } from "./context/AuthContext";
import "./animations.css";
import "./index.css";
import "./responsive.css";
import Agregarsocio from "./pages/Agregarsocio";
import Camcontra from "./pages/Camcontra";
import Error from "./pages/404";
import Escanear from "./pages/Escanear";
import Gestion from "./pages/Gestion";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Sign from "./pages/Sign";
import Socios from "./pages/Socios";
import User from "./pages/User";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/crear" element={<Sign />} />

          <Route element={<RutaProtegida />}>
            <Route path="/home" element={<Home />} />
            <Route path="/horarios" element={<Home />} />
            <Route path="/buscar" element={<Home />} />
            <Route path="/socios" element={<Socios />} />
            <Route path="/socios/:id" element={<Socios />} />
            <Route path="/gestion" element={<Gestion />} />
            <Route path="/gestion/:id" element={<Gestion />} />
            <Route path="/agregarsocio" element={<Agregarsocio />} />
            <Route path="/agregar/:tipo" element={<Agregarsocio />} />
            <Route path="/usuario" element={<User />} />
            <Route path="/escanear" element={<Escanear />} />
            <Route path="/contraseña" element={<Camcontra />} />
          </Route>

          <Route path="*" element={<Error />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
