class HolderAnalyzer:
    def __init__(self):
        self.min_holder_ratio = 0.1  # Mínimo ratio de holders en beneficio
        
    def analyze_distribution(self, symbol: str, holder_data: Dict) -> float:
        """Analiza la distribución de holders y retorna un score"""
        try:
            profit_ratio = holder_data.get('Direcciones de beneficios %', 0)
            breakeven_ratio = holder_data.get('Direcciones "break-even" %', 0)
            loss_ratio = holder_data.get('Direcciones de pérdidas %', 0)
            
            # Calcular score basado en distribución
            score = (profit_ratio * 0.6 + 
                    breakeven_ratio * 0.3 + 
                    (100 - loss_ratio) * 0.1)
            
            return min(100, max(0, score)) / 100
            
        except Exception as e:
            logger.error(f"Error analizando holders para {symbol}: {str(e)}")
            return 0 