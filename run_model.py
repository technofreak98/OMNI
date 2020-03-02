import argparse
import h5py 
import numpy as np
import os
from functools import reduce
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons

import torch
from torch.utils.data import TensorDataset,DataLoader

from preprocess_data import data_read,windowing_and_resampling
from utils import load_model_CNN

def main(args):
    
    preprocessed_patient_data = data_read(args)
    print('-------- Data Acquisition Complete --------')
    windowed_patient_overlap,windowed_patient = windowing_and_resampling(preprocessed_patient_data)
    print('-------- Pre-processing Complete ---------')
    patient_ecg = np.asarray(windowed_patient_overlap['ecg'][0])

    batch_len = 128
    window_size = 5000

    patient_ecg = torch.from_numpy(patient_ecg).view(patient_ecg.shape[0],1,patient_ecg.shape[1]).float()
    input_ecg = TensorDataset(patient_ecg)
    testloader = DataLoader(input_ecg,batch_len)

    SAVED_MODEL_PATH = "model.pt"
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")    
    
    peak_locs = load_model_CNN(SAVED_MODEL_PATH,testloader,device,batch_len,window_size)     

    ### Finding Stored Paths
    save_dir = args.save_dir
    if not(os.path.isdir(save_dir)):
        os.mkdir(save_dir)

    save_path =  save_dir + '/r_peaks_patient_' + str(args.patient_no) + '.csv'
    
    peak_no = np.linspace(1,len(peak_locs),len(peak_locs)).astype(int)
    peak_no = peak_no.reshape(-1,1)
    peak_locs = peak_locs.reshape(-1,1) 
    peak_locs = np.hstack((peak_no,peak_locs))

    pd.DataFrame(peak_locs).to_csv(save_path , header=None, index=None)  
    print('-------- R Peaks Saved --------')

    actual_ecg_windows = np.asarray(windowed_patient['ecg'][0])
    actual_ecg_windows = actual_ecg_windows.reshape(-1,actual_ecg_windows.shape[1])
    if(args.viewer):
        i = 1
        scatter_peak = []
        scatter_peak_1 = []
        ecg_point = []
        ecg_point_1 = []
        k = 0

        peak_locs = peak_locs[:,1]
        for j in range(len(peak_locs)):     
            if(peak_locs[j] < 5000*i):
                scatter_peak.append(peak_locs[j]-5000*(i-1))
                if(i< len(actual_ecg_windows)):
                    ecg_point.append(actual_ecg_windows[i-1,scatter_peak[k]])
                    k = k+1                         
            elif(peak_locs[j] >= 5000*i):
                scatter_peak_1.append(np.asarray(scatter_peak))
                ecg_point_1.append(np.asarray(ecg_point))                     
                scatter_peak = []
                ecg_point = []
                i = i+1
                scatter_peak.append(peak_locs[j]-5000*(i-1))
                k = 0
                if(i< len(actual_ecg_windows)):
                    ecg_point.append(actual_ecg_windows[i-1,scatter_peak[k]])
                    k = k+1
        

        actual_ecg_windows = actual_ecg_windows.transpose(1,0)
        print('.......Displaying..........')
        fig, ax = plt.subplots()
        #t = np.arange(0.0, 5000.0, 1.0)
        s = actual_ecg_windows[:,0]
        l, = plt.plot(s) ## Don't know what lw is
        plt.ylim(ymax = 10, ymin = -3) 
        scat = plt.scatter(scatter_peak_1[0],ecg_point_1[0])
        axcolor = 'lightgoldenrodyellow'
        bar_coor = plt.axes([0.2, 0.9, 0.65, 0.03], facecolor=axcolor)
        ### Change 212 to no o f windows of ECG
        slide = Slider(bar_coor, 'Window_number', 0, actual_ecg_windows.shape[1]-1, valinit=0, valstep = 1)
        def update(val):
            window_no = slide.val
            print(scatter_peak_1[np.int(window_no)])
            print(ecg_point_1[np.int(window_no)])
            #l.set_xdata((window_no-1)*5000:window_no*5000)
            l.set_ydata(actual_ecg_windows[:,np.int(window_no)])
            xx = np.vstack((scatter_peak_1[np.int(window_no)],ecg_point_1[np.int(window_no)]))
            scat.set_offsets(xx.T)
            #scat.set_array (ecg_point_1[np.int(window_no)])
            #scat.set_ydata(scatter_peak_1[np.int(window_no)],ecg_point_1[np.int(window_no)])
            fig.canvas.draw_idle()
        slide.on_changed(update)
        plt.show()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--path_dir',help = 'Path to all the records')
    parser.add_argument('--patient_no',type = int,help = 'Patient used for testing')
    parser.add_argument('--save_dir',help = 'Directory used for saving')
    parser.add_argument('--viewer',type = int, help = 'To view ECG plot: 1, else: 0')

    args = parser.parse_args()

    main(args)
    