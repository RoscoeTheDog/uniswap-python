import functools
from typing import (
    TYPE_CHECKING,
    Callable,
    List,
    Optional,
    TypeVar,
)
from typing import Union

from typing_extensions import Concatenate, ParamSpec

from .constants import ETH_ADDRESS
from .types import AddressLike

if TYPE_CHECKING:
    from .uniswap import Uniswap


T = TypeVar("T")
P = ParamSpec("P")


def check_approval(method: Callable[..., T]) -> Callable[..., T]:
    """Decorator to check if the user is approved for a token. It approves them if they
    need to be approved."""

    @functools.wraps(method)
    def approved(self: "Uniswap", *args: Union[AddressLike, int], **kwargs) -> T:
        # Check to see if the first token is actually ETH or present in kwargs
        token: Optional[AddressLike] = (
            args[0] if args and args[0] != ETH_ADDRESS else kwargs.get('input_token')
        )

        # Check the second token if needed, from args or kwargs
        token_two: Optional[AddressLike] = None
        if method.__name__ in ["make_trade", "make_trade_output"]:
            token_two = (args[1] if len(args) > 1 and args[1] != ETH_ADDRESS else kwargs.get('output_token'))

        # Approve both tokens if needed
        if token:
            is_approved = self._is_approved(token)
            if not is_approved:
                self.approve(token)
        if token_two:
            is_approved_two = self._is_approved(token_two)
            if not is_approved_two:
                self.approve(token_two)

        return method(self, *args, **kwargs)

    return approved


def supports(
    versions: List[int],
) -> Callable[
    [Callable[Concatenate["Uniswap", P], T]], Callable[Concatenate["Uniswap", P], T]
]:
    def g(
        f: Callable[Concatenate["Uniswap", P], T]
    ) -> Callable[Concatenate["Uniswap", P], T]:
        if f.__doc__ is None:
            f.__doc__ = ""
        f.__doc__ += """\n\n
        Supports Uniswap
        """ + ", ".join(
            "v" + str(ver) for ver in versions
        )

        @functools.wraps(f)
        def check_version(self: "Uniswap", *args: P.args, **kwargs: P.kwargs) -> T:
            if self.version not in versions:
                raise Exception(
                    f"Function {f.__name__} does not support version {self.version} of Uniswap passed to constructor"
                )
            return f(self, *args, **kwargs)

        return check_version

    return g
