# EnergyMarket
It simulates a simple energy market using concurrent execution features of Python.



Now we have: HOME <-- message queue --> MARKET <-- shared memory -- WEATHER
                                           ^
                                           |
                                        signal
                                           |
                                       External
                                       
                                       
                                       
Stuff to add:
Make Weather better.
Make the temperature effect energy consumption of homes.
Improve the visualization.
