export default function RetailBackdrop() {
  return <div className="retail-fallback" aria-hidden="true">
    {['THE CORNER', 'DAILY GOODS', 'MARKET & CO.', 'LOCAL FINDS'].map((name, i) => <div className={'retail-facade facade-' + i} key={name}>
      <div className="retail-windows"><i /><i /></div><strong>{name}</strong><div className="retail-awning" /><div className="retail-display"><i /><i /><i /></div>
    </div>)}
    <span className="retail-sale">SALE</span>
  </div>;
}
