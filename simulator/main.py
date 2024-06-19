import sys
import asyncio
from time import sleep
from src.simulator import Simulator


async def main():
    simulator: Simulator = Simulator()
    await simulator.start()
    sleep(1)
    await simulator.finish()


if __name__ == "__main__":
    asyncio.run(main())
