import sys

import anyio
import dagger


async def main():
    config = dagger.Config(log_output=sys.stdout)

    # initialize Dagger client
    async with dagger.Connection(config) as client:
        pip_cache = client.cache_volume("pip")

        python = (
            client.container()
            .from_("python:3.7-slim")
            .with_mounted_directory(
                "/src", client.host().directory(".", exclude=["docs/", "ci/"])
            )
            .with_mounted_cache("/src/.pip/cache", pip_cache)
        )

        test_runner = python.with_workdir("/src").with_exec(
            ["pip", "install", "--cache-dir=/src/.pip/cache", "-e", ".[tests]"]
        )
        results = test_runner.with_exec(
            ["pytest", "--cov", "./apinator", "--cov-report", "term-missing"]
        )
        await results.exit_code()


if __name__ == "__main__":
    anyio.run(main)
