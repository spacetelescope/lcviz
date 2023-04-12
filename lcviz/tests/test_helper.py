import astropy.units as u

from lcviz import LCviz


def test_load_data():
    '''Simple test to load some test data'''
    time = [0,1,2,3,4,5,6,7,8,9] * u.s
    flux = [9,8,7,6,5,4,3,2,1,0] * u.Jy

    lcviz = LCviz()
    lcviz.load_data(time=time, flux=flux, data_label="mydata")
