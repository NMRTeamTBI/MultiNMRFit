from tkinter import * 
from tkinter import messagebox 
import tkinter.font as tkFont
import tkinter as tk
import pandas as pd
from random import randint
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MyOptionMenu(tk.OptionMenu):
    def __init__(self, master, status, *options):
        self.var = tk.StringVar(master)
        self.var.set(status)
        tk.OptionMenu.__init__(self, master, self.var, *options)
        self.config(font=('calibri',(10)),bg='white',width=12)
        self['menu'].config(font=('calibri',(10)),bg='white')

################################################################
# Definitions for the peak selection and clustering
################################################################

def saveinfo(r,dic):
    Res.Peak_Amp = dic['Intensity']
    Res.ppm_H_AXIS = dic['Peak_Position']
    Res.Cluster = [i.get() for i in dic["Cluster"]]
    Res.Selection = [i.get() for i in dic["Selection"]]
    r.destroy()
    plt.close()

def save_nt(r, dic, new_threshold):
    for n in dic['th']:
        nt = n.get()
    new_threshold.nt.loc[1] = nt
    r.destroy()
    plt.close()
    return new_threshold

def Exit(r):
    r.destroy()
    plt.close()

def opennewwindow(PeakPicking_Threshold, pp_results,figure,pts_Color,Res,new_threshold):
    newwindow = tk.Tk()
    newwindow.title('Peak Picking Visualisation and Validation')
    graph = FigureCanvasTkAgg(figure, master=newwindow)
    canvas = graph.get_tk_widget()
    canvas.grid(row=0, column=0,columnspan = 8,rowspan=1)

    pp_names = ['ppm_H_AXIS','Peak_Amp']
    data_cols_names = ['1H ppm','Peak Intensity','Selection','Cluster']
    # Multiplicity_Choice = ('Singlet','Doublet')

    for c in range(len(data_cols_names)):
        tk.Label(newwindow, text=str(data_cols_names[c]), ).grid(column=c+1, row=2)

    dic = {
        'Cluster': [],
        'Selection': [],
        'Intensity':[],
        'Peak_Position':[]
    }
    dic_par = {
        'th':[]
    }
    npeaks = len(pp_results)
    for i in range(npeaks):
        tk.Label(newwindow, text="Peak "+str(i+1),fg=pts_Color[i]).grid(column=0, row=i+3)
        en = tk.Entry(newwindow,justify = "center")

        # Button for peak selection
        check_resultat = tk.IntVar()
        checkbutton1=Checkbutton(newwindow, var=check_resultat,onvalue=0,offvalue=1)
        checkbutton1.grid(row=i+3,column=len(data_cols_names)-1)
        checkbutton1.var=check_resultat
        dic['Selection'].append(check_resultat)
        print(check_resultat.get())

        # # Menu to choose mutliplicity
        # v = tk.StringVar()
        # v.set('Multiplicity')
        # dic['Multiplicity'].append(v)
        # OptionMenu1 = OptionMenu(newwindow, v, *Multiplicity_Choice)
        # OptionMenu1.grid(row=i+3,column=len(data_cols_names)-1)

        # Clustering
        en_cluster = tk.Entry(newwindow,justify = "center")
        en_cluster.insert(0, 0)
        dic['Cluster'].append(en_cluster)
        en_cluster.grid(column=len(data_cols_names),row=i+3,ipadx=5)

        for c in range(len(pp_names)):
            col = pp_names[c]
            en_c = tk.Entry(newwindow,justify = "center")
            data = pp_results.iloc[i].loc[col]
            if col == 'ppm_H_AXIS':
                dic['Peak_Position'].append(data)
            if col == 'Peak_Amp':
                dic['Intensity'].append(data)
            en_c.insert(0, round(data,3))
            en_c.grid(column=c+1,row=i+3,sticky=tk.N+tk.S+tk.E+tk.W)
    
    disp = Entry(newwindow, readonlybackground="white")
    tk.Label(newwindow, text="Threshold", fg='#f00').grid(column=0, row=1)
    disp.insert(0, PeakPicking_Threshold)
    disp.grid(column=1, row=1)
    dic_par['th'].append(disp)

    tk.Button(newwindow, text="Refresh & Close", fg = "orange", command=lambda: save_nt(newwindow, dic_par, new_threshold)).grid()  
    tk.Button(newwindow, text="Save & Close", fg = "blue", command=lambda: saveinfo(newwindow, dic)).grid() 
    tk.Button(newwindow, text="Exit", fg = "black", command=lambda: Exit(newwindow)).grid() 

    newwindow.mainloop()

Res = pd.DataFrame(columns=['ppm_H_AXIS','Peak_Amp','Selection','Cluster'])

def main_window(x_Spec,y_Spec,PeakPicking_Threshold,PeakPicking_data):

    n_peak = len(PeakPicking_data)
    if n_peak >=10:
        PeakPicking_data = PeakPicking_data.sort_values(by='Peak_Amp', ascending=False).head(10)
        PeakPicking_data = PeakPicking_data.sort_values(by='ppm_H_AXIS', ascending=True)
        n_peak = len(PeakPicking_data)

    #Res = pd.DataFrame(columns=['ppm_H_AXIS','Peak_Amp','Check','Cluster'],index=np.arange(1,n_peak+1))
    new_threshold = pd.DataFrame(columns=['nt'],index=[1])

    # Create a list of colors
    colors = []
    for i in range(n_peak):
        colors.append('#%06X' % randint(0, 0xFFFFFF))

    #Plot Spectrum with peak picking
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_Spec, y_Spec, '-',color='teal')
    for i in range(n_peak):
        ax.plot(PeakPicking_data.ppm_H_AXIS.iloc[i],PeakPicking_data.Peak_Amp.iloc[i],c=colors[i],ls='none',marker='o')
    ax.axhline(PeakPicking_Threshold,c='r')
    ax.invert_xaxis()
    ax.set_xlabel(r'$^1H$ $(ppm)$')

    opennewwindow(
        PeakPicking_Threshold,
        PeakPicking_data, 
        fig,
        colors,
        Res,
        new_threshold
        )

    return new_threshold, Res