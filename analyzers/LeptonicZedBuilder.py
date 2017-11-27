from heppy.framework.analyzer import Analyzer
from heppy.particles.tlv.resonance import Resonance2 as Resonance
from heppy.analyzers.ResonanceBuilder import ResonanceBuilder

import pprint 
import itertools

class LeptonicZedBuilder(ResonanceBuilder):
    '''Builds a list of Z resonances from an input lepton collection. 
       Elements in this list consist in pairs of leptons. A given lepton can appear
       only in one pair of the list.

    Example:

    from heppy.analyzers.LeptonicZedBuilder import LeptonicZedBuilder
    zeds = cfg.Analyzer(
      LeptonicZedBuilder,
      output = 'zeds',
      leptons = 'leptons',
    )

    * output : resulting Z resonances are stored in this collection, 
    sorted according to their distance to the nominal Z mass. The first 
    resonance in this collection is thus the best one. 
    
    Additionally, a collection zeds_legs (in this case) is created to contain the 
    legs of the best resonance. 

    * leptons : collection of leptons that will be combined into resonances.

    '''

    def __init__(self, *args, **kwargs):
        super(LeptonicZedBuilder, self).__init__(*args, **kwargs)
        self.cfg_ana.leg_collection = self.cfg_ana.leptons

    def get_pdgid(self):
        try:
            pdgid = self.cfg_ana.pdgid
        except AttributeError:
            pdgid = 23
        return pdgid

    

    def matches(self, zed, zeds) :
        for z in zeds:    
            if ( zed.leg1() is z.leg1() or 
                 zed.leg1() is z.leg2() or 
                 zed.leg2() is z.leg1() or 
                 zed.leg2() is z.leg2() ) : 
                return True
		
    def isLeptonic(self, zed) :
        if ( zed.leg1().pdgid() == -zed.leg2().pdgid() ) :
            return True

    def clean(self, resonances):
        zeds = []
        for z in resonances:
           if not self.matches(z, zeds) and self.isLeptonic(z) : zeds.append(z) 

        return zeds
