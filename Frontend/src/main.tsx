
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";

import Home from "./pages/Home";
import Login from "./pages/Login";
import User from "./pages/User";
import Escanear from "./pages/Escanear";
import Sign from "./pages/Sign";
import Error from "./pages/404";
import Socios from "./pages/Socios";
import Agregarsocio from "./pages/Agregarsocio";

import RutaProtegida from "./components/RutaProtegida";

import "./animations.css";
import "./index.css";
import "./responsive.css";

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
            <Route path="/agregarsocio" element={<Agregarsocio />} />
            <Route path="/usuario" element={<User />} />
            <Route path="/escanear" element={<Escanear />} />
          </Route>

         
          <Route path="*" element={<Error />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);
