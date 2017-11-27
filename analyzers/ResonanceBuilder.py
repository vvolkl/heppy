'''Builds L{resonances<heppy.particles.tlv.resonance>}.'''

from heppy.framework.analyzer import Analyzer
from heppy.particles.tlv.resonance import Resonance2 as Resonance

import pprint 
import itertools

mass = {23: 91, 25: 125, 32:200}

class ResonanceBuilder(Analyzer):
    '''Builds L{resonances<heppy.particles.tlv.resonance>}.

    Example:: 

        from heppy.analyzers.ResonanceBuilder import ResonanceBuilder
        zeds = cfg.Analyzer(
          ResonanceBuilder,
          output = 'zeds',
          leg_collection = 'sel_iso_leptons',
          pdgid = 23
        )

    @param output: L{Resonances<heppy.particles.tlv.resonance>} are stored in this collection, 
      sorted according to their distance to the nominal mass corresponding 
      to the specified pdgid. The first resonance in this collection is thus the best one. 
    
      Additionally, a collection zeds_legs (in this case) is created to contain the 
      legs of the best resonance. 

    @param leg_collection: Collection of particles that will be combined into resonances.

    @param pdgid: Pythia code for the target resonance. 
    '''

    def clean(self, resonances):
        """ Filters resonances according to some criteria. No-op in this implementation,
            but may be overridden in derived classes.

            @return resonances: the filtered list of resonances 
        """
        return resonances

    def get_pdgid(self):
        return self.cfg_ana.pdgid
    
    def process(self, event):
        '''Process the event
        
        The event must contain:
         - self.cfg_ana.leg_collection: the input collection of particles
         
        This method creates:
         - event.<self.cfg_ana.output>: collection of resonances
         - event.<self.cfg_ana.output>_legs: the two legs of the best resonance.
        '''
        legs = getattr(event, self.cfg_ana.leg_collection)
        uncleaned_resonances = []
        for leg1, leg2 in itertools.combinations(legs,2):
            uncleaned_resonances.append( Resonance(leg1, leg2, self.get_pdgid()) )

        resonances = self.clean(uncleaned_resonances)
        # sorting according to distance to nominal mass
        try:
            nominal_mass = self.cfg_ana.nominal_mass
        except AttributeError: # if not specified explicitly, try to look it up according to pdgid
            nominal_mass = mass[self.get_pdgid()]

        resonances.sort(key=lambda x: abs(x.m()-nominal_mass))
        setattr(event, self.cfg_ana.output, resonances)
        # getting legs of best resonance
        legs = []
        if len(resonances):
            legs = resonances[0].legs
        setattr(event, '_'.join([self.cfg_ana.output, 'legs']), legs)
                
