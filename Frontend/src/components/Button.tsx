interface BotonProps {
  texto: string;
  clase: string;
  onClick: () => void;
}

function Boton({ texto, clase, onClick }: BotonProps) {
  return (
    <button className={clase} onClick={onClick}>
      {texto}
    </button>
  );
}

export default Boton;