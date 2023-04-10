__all__ = ['primes', 'do_primes']


def primes(imax):
    """Returns prime numbers up to ``imax``.

    Parameters
    ----------
    imax : int
        The number of primes to return. This should be less or equal to 10000.

    Returns
    -------
    result : list
        The list of prime numbers.

    Raises
    ------
    ValueError
        Invalid ``imax``.

    Examples
    --------
    >>> from lcviz import primes
    >>> primes(2)
    [2, 3]

    """

    p = list(range(10000))
    result = []
    k = 0
    n = 2

    if imax > 10000:
        raise ValueError("imax should be <= 10000")

    while len(result) < imax:
        i = 0
        while i < k and n % p[i] != 0:
            i = i + 1
        if i == k:
            p[k] = n
            k = k + 1
            result.append(n)
            if k > 10000:  # pragma: no cover
                break
        n = n + 1

    return result


def do_primes(n, usecython=False):
    """Returns prime numbers up to ``n``.

    Parameters
    ----------
    n : int
        The number of primes to return. This should be less or equal to 10000.

    usecython : bool
        If `True`, use Cython implementation.

    Returns
    -------
    result : list
        The list of prime numbers.

    Raises
    ------
    NotImplementedError
        Cython implementation unavailable.

    See Also
    --------
    primes

    Examples
    --------
    >>> from lcviz import do_primes
    >>> do_primes(2)
    [2, 3]

    """
    if usecython:
        raise NotImplementedError(
            "This template does not have the example C code included.")
    else:
        # Using pure python primes
        return primes(n)


def main(args=None):
    """Driver for command line interface."""
    import argparse
    from time import time

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--use-cython', dest='cy', action='store_true',
                        help='Use the Cython-based Prime number generator.')
    parser.add_argument('-t', '--timing', dest='time', action='store_true',
                        help='Time the Prime number generator.')
    parser.add_argument('-p', '--print', dest='prnt', action='store_true',
                        help='Print all of the Prime numbers.')
    parser.add_argument('n', metavar='N', type=int,
                        help='Get Prime numbers up to this number.')

    res = parser.parse_args(args)

    pre = time()
    primes = do_primes(res.n, usecython=res.cy)
    post = time()

    print(f'Found {len(primes)} prime numbers')
    print(f'Largest prime: {primes[-1]}')

    if res.time:
        print(f'Running time: {post - pre} s')

    if res.prnt:
        print(f'Primes: {primes}')
