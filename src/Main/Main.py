'''
Created on 20 Feb 2014

@author: Wiz
'''
import sys
import numpy as np
import decimal
from PySQS.CatchMod import CatchMod


def main(args):
    print args
    print "Hello World"

if __name__ == '__main__':
    pass
    np.set_printoptions(4, threshold='nan')
    
    importData = np.genfromtxt('C:\Dissertation\IW_Outputs\Runs_13_2\Runs_13_2_W3_Q.csv', delimiter = ',')
    dwfData = np.genfromtxt('C:\Dissertation\Matlab Files\dwfData.csv', delimiter = ',')
    cm = CatchMod(importData, dwfData, 'CM_ID1_A25_732', 79887621.1, 300)

    
