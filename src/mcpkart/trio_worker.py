"""Private three-kart ghost worker; keeps HTTP and model code outside physics."""

from .duel_runtime import DuelRuntime
from .duel_worker import main


def trio_runtime(**kwargs):
    return DuelRuntime(trio=True, **kwargs)


if __name__ == "__main__":
    main(runtime_factory=trio_runtime)
