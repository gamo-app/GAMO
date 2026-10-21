import Icon from "../components/Icon";
import {  useNavigate } from "react-router-dom";
import Main from "../components/Main";
function Error() {
  const navigate = useNavigate();
  
  return (
    <Main>
      

      <section className="centro">
     <div className="listabloques">
        <Icon tipo={12} tamaño={10}></Icon>
        <h1>404</h1>
        <h2>Pagina no encontrada</h2>
       <button className="azul" onClick={() => navigate(-1)}>
          Volver atras
        </button>
     </div>
   
      </section>

   </Main>
  );
}

export default Error