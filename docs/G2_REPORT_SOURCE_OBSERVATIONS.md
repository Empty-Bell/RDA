# Report source-observation projection

Each report row now includes `energyguide_source_observations`. Each entry copies
the source fact's document URL, PDF SHA256, document status, annual energy
observation, capacity observation and evidence IDs. It does not add a model value,
SKU match, delta, tolerance, severity or assessment status.

The report preserves unavailable observations as their original state. A fresh PDF
that no longer matches a reviewed annotation remains `NOT_OBSERVED` rather than
becoming a source or regulatory failure.

The report regression creates an EnergyGuide source fact with 585 kWh/year and
22.0 Cubic Feet, then proves the report copies both measurements and evidence ID
unchanged while finding count stays zero and assessment remains disabled. Hosted
run 35182804474 passed the G1 fixture suite; hosted run 35182804467 passed the
G2 source contracts on Ubuntu 24.04.
