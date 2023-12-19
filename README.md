nextract pulls statistics from the Power Systems HMC by using the HMC Performance and Capacity Monitoring REST API in to four useful formats or graphs. 
This is called "nextract plus" as it extracts performance statistics, energy statistics (Temperature and Watts) and Shared Storage Pools (SSP) statistics.

This nextract tool is not an IBM product, so there is no IBM support. 
It is the personal project of the author.
All of the program Python source code and sample data is available in the download file.

About nextract_plus generally:
 - Extracts data from the Hardware Management Console (HMC) REST API and is written in Python 3.
 - You must have a recent version of Python available. Python 2.x is not supported at all.
 -  This version gets every available Performance Statistics for Power Servers, Virtual I/O Server, Hypervisor, Logical Partition (virtual machine) and writes it to an InfluxDB for graphing with Grafana (or other tools).
 - Included in this version are the Python programs for Power Systems energy (electrical Watts and Temperatures) and Shared Storage Pools (SSP).
 - The matching Grafana dashboard for the performance statistics offers 70+ performance graphs many covering multiple statistics, 24 information single statistic, or configuration detail panels.

The statistic data can be saved to:
- Saved to a comma-separated values file (CSV).
- Used to generated Google chart webpages of graphs.
- More importantly save the data to the InfluxDB time-series database for graphing by Grafana.
- This later option is the recommended use as it allows long-term data collection of the statistics and flexible user graphing.

The Python programs are:
 - nextract_plus.py for the Performance statistics.
 - nextract_energy.py for the Watts and temperatures.
 - nextract_ssp.py for the Shard Storage Pool (SSP).
 - hmc_pcm.py a Python module for used to hide the complexity of the HMC REST API as it returns multiple level XML, file name lists, and JSON data.
 - nchart.py for generating the webpage (.html file) that uses JavaScript calls to the Google Chart library for graphing.
 - Also, some sample config files.
 - A single JSON file is used for the parameters of all the Python programs.

Notes:
 - I am using Red Hat Enterprise 8 and AIX 7.3. You could use other versions of Linux but Nigel can't offer full support on them.
 - AIX 7.3 includes Python 3.9 but you can install Python on AIX 7.2 from the AIX open source toolbox.
 - nextract_plus draws data from the HMC so it needs an HMC user account to log in.
 - It is assumed you are using HMC version 9 or 10 on mostly POWER8, POWER9, and Power10 servers.
 - To make it obvious in a list of user accounts on the HMC, I use an account called nextractplus.
 - nextract_plus.py (in the diagram) also includes the nextract_energy.py and nextract_ssp.py programs.
 - All the programs can share a single JSON format configuration file.  I use one config per HMC to keep things simple.
 - Depending on the config the data is saved to a .csv file, a .html webpage file or directly into InfluxDB.

