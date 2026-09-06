export default function StockRow({ stock, onRemove }) {
  return <div className="detail-stock-row"><div><strong>{stock.symbol}</strong><span>{stock.company_name}</span></div><div className="stock-row-actions"><span>{stock.exchange}</span><button className="remove-stock-button" type="button" onClick={() => onRemove(stock)}>Remove</button></div></div>
}
