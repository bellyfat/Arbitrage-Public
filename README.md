# Arbitrage (Public Version)

Finds cryptocurrency triangular arbitrage opportunities.
System is modeled as a networkx graph to detect profitable arbitrage cycles.
Profitable cycles can be tracked over time and considers factors including:
    + Confirmation times
    + Exchange receive and send times (imputed)
    + Transaction fees
