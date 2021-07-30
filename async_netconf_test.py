"""
Author: IPvZero
Simple async NETCONF test
"""
import os
import asyncio
import yaml
from jinja2 import Environment, FileSystemLoader
from scrapli_netconf.driver import AsyncNetconfDriver
from rich import print as rprint
from inv import DEVICES

username = os.environ["USERNAME"]
password = os.environ["PASSWORD"]


def generate_config(device):
    """
    Load yaml from host vars for each device in list.
    Render config via jinja2
    """
    hostname = device["hostname"]
    config_data = yaml.safe_load(open(f"host_vars/{hostname}.yaml"))
    env = Environment(
        loader=FileSystemLoader("./templates"), trim_blocks=True, lstrip_blocks=True
    )
    template = env.get_template("ospf.j2")
    configuration = template.render(config_data)
    return configuration


async def push_config(device):
    """
    Coroutine to open connection and send RPCs
    """
    hostname = device["hostname"]
    async with AsyncNetconfDriver(
        host=device["host"],
        auth_username=username,
        auth_password=password,
        auth_strict_key=False,
        transport="asyncssh",
    ) as conn:
        lock_result = await conn.lock(target="candidate")
        cfg = generate_config(device)
        configs_result = await conn.edit_config(config=cfg, target="candidate")
        commit_result = await conn.commit()
        unlock_result = await conn.unlock(target="candidate")
    return hostname, lock_result, configs_result, commit_result, unlock_result


async def main():
    """
    Main coroutine
    """
    coroutines = [push_config(device) for device in DEVICES]
    results = await asyncio.gather(*coroutines)
    for result in results:
        rprint(f"[green]==== {result[0]} ====[/green]")
        rprint("[cyan]NETCONF LOCK[/cyan]")
        print(f"{result[1].result}")
        rprint("[cyan]NETCONF EDIT CONFIG[/cyan]")
        print(f"{result[2].result}")
        rprint("[cyan]NETCONF COMMIT[/cyan]")
        print(f"{result[3].result}")
        rprint("[cyan]NETCONF UNLOCK[/cyan]")
        print(f"{result[4].result}\n\n")


asyncio.run(main())
