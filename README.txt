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
Make sunny effect the energy production of homes.
Show all the budgets of homes in one single graph with Market process.
