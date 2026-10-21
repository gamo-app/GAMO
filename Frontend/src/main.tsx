import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Home from './pages/Home'
import Login from './pages/Login'
import User from './pages/User'
import Escanear from './pages/Escanear'
import Sign from './pages/Sign'
import Error from './pages/404'
import Gestion from './pages/Gestion'
//import Socios from './pages/Socios'
import Agregarsocio from './pages/Agregarsocio'

// @ts-expect-error El módulo JSX no tiene declaración de tipos
import Admin from './pages/admin.jsx'
// @ts-expect-error El módulo JSX no tiene declaración de tipos
import Recepcion from './pages/recepcion'
import Camcontra from "./pages/Camcontra"
import Header from "./components/Header"
import Main from "./components/Main"
import './animations.css'
import './index.css'
import './responsive.css'
import Prueba from './pages/prueba.js'
import Layout from "./components/Layout";
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />

        <Route element={<Layout />}>
          <Route path="/*" element={<Error />} />
          <Route path="/p" element={<Prueba />} />
        </Route>

        <Route path="/crear" element={<Sign />} />
        <Route path="/home" element={<Home />} />
        <Route path="/contraseña" element={<Camcontra />} />
        <Route path="/horarios" element={<Home />} />
        <Route path="/buscar" element={<Home />} />
    {/*    <Route path="/socios" element={<Socios />} />
        <Route path="/socios/:id" element={<Socios />} />*/}
        <Route path="/gestion" element={<Gestion />} />
        <Route path="/gestion/:id" element={<Gestion />} />
        <Route path="/agregar/:tipo" element={<Agregarsocio />} />
        <Route path="/usuario" element={<User />} />
        <Route path="/escanear" element={<Escanear />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/recepcion" element={<Recepcion />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>
)