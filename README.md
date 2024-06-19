# tiger-simulator

This simulator has been built as part of a Bachelors thesis by Piotr Blinowski,
Szymon Mrozicki, Szymon Potrzebowski, Karol Wąsowski, under the supervision of
Janina Daszkiewicz-Mincel Ph.D. If you want to read the thesis, click
[here](https://github.com/technical-tigers/tiger-simulator).

## Running the simulator

To run the simulator, first place a scheduler implementation under the
`scheduler/` directory and make sure it includes a Dockerfile with instructions
on how to start it. The scheduler should listen for connections on the 2137 port.

Prerequisites:
- `docker`
- `docker compose`

To start a simulation run:

```
docker compose up --build
```

## Simulator variants

There are two branches in this repository:
- `main-llm` - contains support for request batching,
- `main-dnn` - base simulator with no batching support.

# Credits

- `wait-for-it` - https://github.com/vishnubob/wait-for-it

