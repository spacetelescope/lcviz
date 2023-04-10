import pytest

from lcviz.example_mod import primes, do_primes, main


def test_primes():
    assert primes(10) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def test_imax_too_big():
    with pytest.raises(ValueError):
        primes(10001)


def test_no_cython():
    with pytest.raises(NotImplementedError):
        do_primes(2, usecython=True)


def test_cli(capsys):
    main(args=['-tp', '2'])
    captured = capsys.readouterr()
    assert captured.out.startswith('Found 2 prime numbers')
    assert len(captured.err) == 0
