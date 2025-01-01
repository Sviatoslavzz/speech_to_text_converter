import asyncio
from pathlib import Path

from utils import convert_to_m4a


async def convert():
    res, path_ = await asyncio.to_thread(convert_to_m4a, Path("../saved_files/test_1.mp4"))
    print(res)
    print(path_)

def main():
    asyncio.run(convert())


main()
