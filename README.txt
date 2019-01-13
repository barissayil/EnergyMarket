# EnergyMarket
It simulates a simple energy market using concurrent execution features of Python.



Now we have: HOME <-- message queue --> MARKET <-- shared memory -- WEATHER
                                           ^
                                           |
                                        signal
                                           |
                                       External
                                       
                                       
                                       
Stuff to add:
Stabilize the energy price.
Make Weather better.
Make the temperature effect energy consumption of homes.
Make External bettter by adding some probabilistic stuff for the events.
Improve the visualization.
