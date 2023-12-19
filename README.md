nextract pulls statistics from the Power Systems HMC by using the HMC Performance and Capacity Monitoring REST API in to four useful formats or graphs. 
This is called "nextract plus" as it extracts performance statistics, energy statistics (Temperature and Watts) and Shared Storage Pools (SSP) statistics.

This nextract tool is not an IBM product, so there is no IBM support. 
It is the personal project of the author.
All of the program Python source code and sample data is available in the download file.

About nextract_plus generally:
 - Extracts data from the Hardware Management Console (HMC) REST API and is written in Python 3.
 - You must have a recent version of Python available. Python 2.x is not supported at all.
o This version gets every available Performance Statistics for Power Servers, Virtual I/O Server, Hypervisor, Logical Partition (virtual machine) and writes it to an InfluxDB for graphing with Grafana (or other tools).
o Included in this version are the Python programs for Power Systems energy (electrical Watts and Temperatures) and Shared Storage Pools (SSP).
o The matching Grafana dashboard for the performance statistics offers 70+ performance graphs many covering multiple statistics, 24 information single statistic, or configuration detail panels.

The statistic data can be saved to:
o Saved to a comma-separated values file (CSV)
o Used to generated Google chart webpages of graphs
o More importantly save the data to the InfluxDB time-series database for graphing by Grafana.
o This later option is the recommended use as it allows long-term data collection of the statistics and flexible user graphing.
