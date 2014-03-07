'''
Created on 20 Feb 2014

@author: Wiz
'''
import numpy as np
from decimal import * 



class CatchMod(object):
    

        
    def movingaverage(self, data, windowsize):
        window = np.ones(int(windowsize))/float(windowsize)
        return np.convolve(data, window, 'same')
    
    def time(self,timestep):
        time = np.zeros(self.numPoints, dtype = 'int')
        for ii in range(0,self.numPoints):
            time[ii] = ii * timestep
        return time
    
    def riseflatfall(self):
        
        riseflatfall = np.zeros((self.numPoints,3), dtype='int')
        for ii in range (1, self.numPoints):
            prevValue = self.flowData[ii - 1]
            currValue = self.flowData[ii]
            if currValue > prevValue:
                riseflatfall[ii,0] = 1
            elif currValue == prevValue:
                riseflatfall[ii,1]= 1
            elif currValue < prevValue:
                riseflatfall[ii,2] = 1
        
        return riseflatfall
            
    def findPeak(self,data):
        outData = np.zeros((self.numPoints,5),dtype='int')
        peakData = np.zeros((0,2))
    
        for ii in range(2, self.numPoints - 1):
            selection6 = data[ii-2:ii+1:1][:,0:2:1]
            selectionNextRow = data[ii+1,1:3:1]
            selectionNext6Flat = data[ii+1:ii+7:1,1]
            selectionNext4Fall = data[ii:ii+4:1,2]
            if np.sum(selection6) == 3:
                outData[ii,0] = 1
            if np.sum(selectionNextRow) == 1:
                outData[ii,1] = 1
            if np.sum(selectionNext6Flat) == 6:
                outData[ii,2] = 1
            if np.sum(selectionNext4Fall) >=3 :
                outData[ii,3] = 1
                
            if outData[ii,0] == 1 and outData[ii,1] == 1 and (outData [ii, 2] == 1 or outData[ii,3]) == 1:
                outData[ii,4] = 1
                newRow = np.zeros((1,2))
                newRow[0,0] = self.time[ii]
                newRow[0,1] = self.flowData[ii]
            
                peakData = np.vstack([peakData,newRow])  
                
        return peakData
    
    def cellT2S2(self,timeStep):
        tenHourPoints = (36000 / timeStep)+1
        tenHourData = self.flowData[:tenHourPoints]
        lookRow = 0
        peaks30Percent = np.zeros(self.numPoints)
        
        for ii in range (0,self.numPoints):
            if ii == 0:
                peaks30Percent[ii]=0
                
            if self.time[ii] == self.peaks[lookRow,0]:
                newPeakCheck = self.peaks[lookRow,1]
                oldPeakVal = peaks30Percent[ii-1]*1.3
                if newPeakCheck > oldPeakVal:
                    peaks30Percent[ii] = newPeakCheck
                else:
                    peaks30Percent[ii] = peaks30Percent[ii-1]
                 
                if lookRow < self.peaks.shape[0]-1:
                    lookRow += 1
            else:
                peaks30Percent[ii] = peaks30Percent[ii-1]
                
        if np.max(peaks30Percent) > 0.7*np.max(tenHourData):
            valS2 = float(np.max(peaks30Percent))
        else:
            valS2 = float(np.max(tenHourData))
        
        row = np.where(self.flowData == valS2)
        timeVal = int(self.time[row])
        return  (timeVal, valS2)
        
    def cellH2I2(self, timeStep, T2S2):
        '0. Time, 1. Flow, 2. 5avFlow, 3. Rising, 4. Flat, 5. Falling, 6. RiseRate,' 
        '7. 5%incr, 8. 5% Decrease, 9. StartTime (colH), 10. End Time (colL)'
        data = np.column_stack((self.time, self.flowData,self.avFlowData,self.riseflatfall))
        newCol = np.zeros((self.numPoints,3))
        
        for ii in range (1,data.shape[0]):
            newCol[ii,0]= (data[ii,2] - data[ii-1,2]) / timeStep
            if newCol[ii,0]> newCol[ii-1,0]*1.05:
                newCol[ii,1] = 1
            if newCol[ii,0]<=0.9*newCol[ii-1,0]:
                newCol[ii-1,2] = 1

        data = np.hstack((data,newCol,))
        
        newCol = np.zeros((self.numPoints,1))
        for ii in range(1,data.shape[0]):
            try:
                nextRowFlag = data[ii+1,7]
                nextThreeRowFlag = np.sum(data[ii+1:ii+4,3])
                nextSixRowFlag = np.sum(data[ii:ii+6,3])
                nextRising = data[ii+1,3]
            except IndexError:
                print '5% Incr Next Row Error', ii

            if data[ii,2]>=np.max(data[:,2])*0.05:
                if nextRowFlag == 1:
                    if nextThreeRowFlag >= 2:
                        if nextRising == 1:
                            newCol[ii] = data[ii,0]
                else:
                    if nextSixRowFlag >=3:
                        if nextRising == 1:
                            newCol[ii] = data[ii,0]
            
        startTime = np.min(newCol[np.nonzero(newCol)])
        row = np.where(self.time == startTime)
        startFlow = float(self.flowData[row[0]])
            
        data = np.hstack((data, newCol))
        
        print 'Start Time H2:', startTime, 'Start Flow I2:', startFlow
        
        
        newCol = np.zeros((data.shape[0],1))
        for ii in range (1,data.shape[0]):
            if data[ii,0]> startTime:
                if data[ii,8] ==1:
                    try:
                        sumNextFive = np.sum(data[ii+1:ii+6,7])
                    except:
                        pass
                    if sumNextFive < 3:
                        if startFlow >= data[ii,1]:
                            pass
                        else:
                            newCol[ii,0] = data[ii,0]
        
        data = np.hstack((data, newCol))
        endTimes = newCol[np.nonzero(newCol)]
        peakTime = np.min(endTimes)
        row = np.where(data == peakTime)
        peakFlow = data[row[0],1][0]
        
        T2 = T2S2[0]
        S2 = T2S2[1]
        
        peakTimeRise = (peakFlow - startFlow)/(peakTime - startTime)
        T2S2Rise = (S2 - startFlow)/(T2 - startTime)
        
        if np.count_nonzero(data[:,10])==0:
            L2 = T2
            M2 = S2
        else:
            if peakTimeRise > T2S2Rise:
                L2 = peakTime
                M2 = peakFlow
            else:
                if np.count_nonzero(data[:,10])>0:
                    secondSmallestTime = endTimes[1]
                    row = np.where(data==secondSmallestTime)
                    secondSmallestFlow = data[row[0],1][0]
                    
                    secondPeakTimeRise = (secondSmallestFlow - startFlow)/(secondSmallestTime - startTime)
                    if secondPeakTimeRise > T2S2Rise:
                        L2 = secondSmallestTime
                        M2 = secondSmallestFlow
                    else:
                        L2 = T2
                        M2 = S2
                else:
                    L2 = T2
                    M2 = S2

        return (startTime, startFlow, L2, M2)    
        
        
              
    def dwfFlowProfile(self, data, timeStep):
        timeData = np.round(86400*data[3:,0],0)
        flowData = data[3:,1]
        TSSconc = 390
        BODconc = 172
        AMMconc = 47
        
        numDayRows = 86400/timeStep
        flowProfile = np.zeros((numDayRows,8), dtype =float)
        flowProfile[:,0] = self.time[:numDayRows]
        
        for ii in range (0,flowProfile.shape[0]):
            timeVal = flowProfile[ii,0]         
            if timeVal % 3600 == 0:
                row = np.where(timeData == timeVal)
                flowProfile[ii,1] = flowData[row]
                curFlow = flowData[row]
                try:
                    nextFlow = flowData[row[0] + 1]
                except IndexError:
                    nextFlow = flowData[0]
            else:
                hrTime = (timeVal % 3600)
                flowChange = (nextFlow - curFlow)/3600
                flowVal = (flowChange * hrTime) + curFlow
                flowProfile[ii,1] = flowVal
            
            flowProfile[ii,2] = TSSconc
            flowProfile[ii,3] = flowProfile[ii,1]*TSSconc
            flowProfile[ii,4] = BODconc
            flowProfile[ii,5] = flowProfile[ii,1]*BODconc
            flowProfile[ii,6] = AMMconc
            flowProfile[ii,7] = flowProfile[ii,1]*AMMconc
            
        return flowProfile
    
    def fileDump(self, flow, profile, name):
        sizeProfile = profile.shape
        
        outData = np.zeros((self.numPoints, sizeProfile[1]+1), dtype = Decimal)
        
        for ii in range(0, self.numPoints):
            outData[ii,0] = self.time[ii]
            
            outData[ii,1] = flow[ii]
            timeVal = outData[ii,0] % 86400
            row = np.where(profile == timeVal)
            for col in range (1,8):
                outData[ii, col+1] = profile[row[0], col]
            
        'Time, Flow, Dry Weather Flow Profile, TSS Conc, TSS Load, BOD Conc, BOD Load, Ammonia Conc, Ammonia Load'
        np.savetxt(name + '.csv', outData, delimiter = ",", fmt='%7.5g')
        
    def pollutionCalcs(self, timeFlowData, T2S2, dwfProfile):
        startTime = timeFlowData[0] #H2
        startFlow = timeFlowData[1] #I2
        peakTimeL2 = timeFlowData[2]  #L2
        peakFlow = timeFlowData[3]  #M2
        peakTimeT2 = T2S2[0]        #T2
        
        k = 1124
        a = 0.26
        b = 0.29
        ADWP = 120
        c = 31400
        d = -1.17
        
        if startTime+peakTimeL2 ==0:
            flowRise = 0
        else:
            flowRise = (peakFlow - startFlow)/((peakTimeL2 - startTime)/60)
            if flowRise < 0:
                flowRise = 0
        
        TSSPeak = k*(ADWP**a)*(flowRise**b)
        percentTimeToPeak = 100
        timeToTSSPeak = (peakTimeT2 - startTime)*(percentTimeToPeak/100)+startTime
        rateRiseTSS = TSSPeak /(timeToTSSPeak - startTime)
        
        TSSProfile = dwfProfile[:,[0, 1, 2,3]]
        
        # 0. Time, 1. flow
        TSSData = np.column_stack((self.time, self.flowData,np.zeros((self.time.shape[0], 2))))
        
        for ii in range(0,TSSData.shape[0]):
            timeVal = TSSData[ii,0]
            flowVal = TSSData[ii,1]
            lookupVal = timeVal % 86400
            row = np.where(TSSProfile == lookupVal)
            dwfFlow = TSSProfile[row[0],1]
            
            if flowVal < dwfFlow:
                currConc = TSSProfile[row[0], 2]
                currLoad = currConc *flowVal
                TSSData[ii,2] = currConc
                TSSData[ii,3] = currLoad
            else:
                currLoad = TSSProfile[row[0],3]
                TSSData[ii,2] = TSSProfile[row[0],2]
                TSSData[ii,3] = currLoad
                
            if TSSPeak != 0:
                if timeVal > startTime:
                    if timeVal < peakTimeT2:
                        

        
        
        

    def __init__(self, importData, dwfData, moduleName, linkID, timeStep):
        self.inData = importData
        self.linkID = linkID
        self.numLinks = self.inData.shape[1]-2
        self.numPoints = self.inData.shape[0] - 1
        
        self.time = self.time(timeStep)
        
        for ii in range(1,self.numLinks): 
            if self.inData[0,ii]== self.linkID:
                self.colFound = ii
        
        self.flowData = self.inData[1:,self.colFound]
        self.avFlowData = self.movingaverage(self.flowData, 5)
        self.riseflatfall = self.riseflatfall()
        self.peaks = self.findPeak(self.riseflatfall)
        dwfProfile = self.dwfFlowProfile(dwfData, timeStep)
        T2S2 = self.cellT2S2(timeStep)
        timeFlowData = self.cellH2I2(timeStep, T2S2)
        self.pollutionCalcs(timeFlowData, T2S2, dwfProfile)
        
        
        
        self.fileDump(self.flowData, dwfProfile, moduleName)
        