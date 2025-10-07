import sys
import time

from scuq import si, quantities

from mpylab.env import Measure
from mpylab.tools import mgraph
from mpylab.env.univers.AmplifierTest import dBm2W


class GTEM(Measure.Measure):
    def __init__(self):
        super(GTEM, self).__init__()
        self.rawData = {}

    def MeasureField(self,
                     dotfile = None,
                     freqs = None,
                     names = None,
                     SearchPaths = None,
                     leveler=None,
                     leveler_par=None,
                     datafunc = None,
                     p_target = None,
                     dwell_time = None,
                     pin = None):
        
        def __datafunc(data):
            return data   # identity function

        if datafunc is None:
            self.datafunc = __datafunc
        else:
            self.datafunc = datafunc

        if pin is None:
            self.pin = [quantities.Quantity(si.WATT, dBm2W(_dBm)) for _dBm in (-40, -30, -25)]
        else:
            self.pin = [quantities.Quantity(si.WATT, dBm2W(_dBm)) for _dBm in pin]

        if dwell_time is None:
            self.dwell_time = 1
        else:
            self.dwell_time = dwell_time

        if p_target is None:
            self.p_target = quantities.Quantity(si.WATT, 1)
        else:
            self.p_target = quantities.Quantity(si.WATT, p_target)


        if names is None:
            names = {'sg': 'sg',
                     'amp_in': 'amp_in',
                     'amp_out': 'amp_out',
                     'gtem': 'gtem',
                     'pm_fwd': 'pm1',
                     'pm_bwd': 'pm2',
                     'fp': ['fp1']}        

        mg = mgraph.MGraph(dotfile, themap=names.copy(), SearchPaths=SearchPaths)
        if leveler is None:
            self.leveler = mgraph.Leveler
        else:
            self.leveler = leveler
        if leveler_par is None:
            self.leveler_par = {'mg': mg,
                                'actor': mg.name.sg,
                                'output': mg.name.gtem,
                                'lpoint': mg.name.gtem,
                                'observer': mg.name.pm_fwd,
                                'pin': self.pin,
                                'datafunc': self.datafunc,
                                'min_actor': None}
            
        dev_dict = mg.CreateDevices()
        err = mg.Init_Devices()

        mg.RFOn_Devices()
        print("# freq, power, efield")
        for f in freqs:
            stat = mg.EvaluateConditions()
            #print(f'Set Frequency to {f*1e-6:.2f} MHz')
            (minf, maxf) = mg.SetFreq_Devices(f)
            lv = self.leveler(**self.leveler_par)
            pin, pout = lv.adjust_level(self.p_target)
            #print("Output Power:", pout)
            efield = []
            for prb in names['fp']:
                dv = dev_dict[prb]
                err, _efield = dv.GetData()
                efield.append(_efield)
            print(f, pout, efield)
            time.sleep(self.dwell_time)

        stat = mg.RFOff_Devices()
        stat = mg.Quit_Devices()


if __name__ == '__main__':
    from mpylab.tools import spacing

    dotfile = 'gtem-immunity.dot'
    freqs = spacing.linspace(30e6, 4e9, 100e6)
    names = {'sg': 'sg',
                     'amp_in': 'amp_in',
                     'amp_out': 'amp_out',
                     'gtem': 'gtem',
                     'pm_fwd': 'pm1',
                     'pm_bwd': 'pm2',
                     'fp': ['fp1']}
    SearchPaths = ['.', '/home/yuy/dev/MpyConfig/LargeGTEM']

    gtem = GTEM()
    gtem.MeasureField(dotfile=dotfile,
                names=names,
                SearchPaths=SearchPaths,
                freqs=freqs,
                dwell_time=0.01,
                p_target = 0.1)
