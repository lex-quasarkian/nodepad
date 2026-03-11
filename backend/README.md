--> [main project index](../README.md)

## Nodepad Backend ##


## Run Tests locally ##
```sh ./scripts/tests-start.sh```


## Database and Cache ##

Nodepad uses PostgreSQL 18+ .Caching use Redis. 
For database IDs used UUID v7 which allows to sort objects by timestamps.

## Data Structures
For performance Nodes(sublists) stored as adjacency lists with fractional indexing. This gives O(1) on move/insert and O(n) recursive on subtree read.
W
