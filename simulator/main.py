import sys
import asyncio
from time import sleep
from src.simulator import Simulator
from src.utils.logger import set_log_level


async def main():
    simulator: Simulator = Simulator()
    await simulator.start()
    sleep(1)
    await simulator.finish()

if __name__ == "__main__":
    set_log_level()
    asyncio.run(main())
