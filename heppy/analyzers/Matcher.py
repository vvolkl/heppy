'''Particle matcher.
'''
from heppy.framework.analyzer import Analyzer
from heppy.utils.deltar import matchObjectCollection, deltaR

import collections

class Matcher(Analyzer):
    '''Particle matcher. 
    
    Works with any kind of object with a p4 method. 
    
    Simple example configuration:: 
    
        from heppy.analyzers.Matcher import Matcher
        papas_jet_match = cfg.Analyzer(
          Matcher,
          instance_label = 'papas', 
          delta_r = 0.3,
          match_particles = 'gen_jets',
          particles = 'papas_jets'
        )
        
    In this particular case, each jet in "papas_jets" will end up with a new 
    attribute called "match". This attribute can be either the closest gen jet in the 
    "gen_jets" collection in case a gen_jet is found within delta R = 0.3, 
    or None in case a match cannot be found in this cone.
    
    More complex example configuration:: 
    
        papas_particle_match_g2r = cfg.Analyzer(
          Matcher,
          instance_label = 'papas_g2r', 
          delta_r = 0.3, 
          particles = 'gen_particles_stable',
          match_particles = [
            ('papas_rec_particles', None),
            ('papas_rec_particles', 211),
            ('papas_rec_particles', 130),
            ('papas_rec_particles', 22)
          ] 
          )
          
    In this case, each gen particle in gen_particles_stable will end up with the following 
    new attributes: 
      - "match"    : closest reconstructed particle in "papas_rec_particles", if any. 
      - "match_211": closest reconstructed particle of pdgId 211 in "papas_rec_particles", 
                     if any. 
      - etc. 
 

    TODO: Colin
    ===========
    
    as well adapted, but probably better to do something more modular.
    for example::
    
        papas_jet_match = cfg.Analyzer(
          Matcher,
          instance_label = 'gen_jets_match', 
          delta_r = 0.3,
          match_particles = 'gen_jets',
          particles = 'papas_jets'
        )
    
    would create for each papas_jet: papas_jet.gen_jets_match
    that is a match object with 2 attributes: particle, distance
    in the more complicated case, just need to use a Selector to select the particles,
    and have several Matcher instances 

    note: one cannot attach the distance to the matched particle as 
    the match particle can be matched to another object... 

    @param particles: collection containing the particles to be matched. 
    @param match_particles: Name of the collection containing the particles where a match 
               is to be found. 
    '''
    
    def beginLoop(self, setup):
        super(Matcher, self).beginLoop(setup)
        self.match_collections = []
        if isinstance( self.cfg_ana.match_particles, basestring):
            self.match_collections.append( (self.cfg_ana.match_particles, None) )
        else:
            self.match_collections = self.cfg_ana.match_particles
        
        
    def process(self, event):
        '''process event
        
        The event must contain:
         - self.cfg_ana.particles: the particles to be matched
         - self.cfg_ana.match_particles: the particles in which the match has to be found
         
        Modifies the particles in event.<self.cfg_ana.particles>
        '''
        particles = getattr(event, self.cfg_ana.particles)
        # match_particles = getattr(event, self.cfg_ana.match_particles)
        for collname, pdgid in self.match_collections:
            match_ptcs = getattr(event, collname)
            match_ptcs_filtered = match_ptcs
            if pdgid is not None:
                match_ptcs_filtered = [ptc for ptc in match_ptcs
                                       if ptc.pdgid()==pdgid]
            pairs = matchObjectCollection(particles, match_ptcs_filtered,
                                          self.cfg_ana.delta_r)
            for ptc in particles:
                matchname = 'match'
                if pdgid: 
                    matchname = 'match_{pdgid}'.format(pdgid=pdgid)
                match = pairs[ptc]
                setattr(ptc, matchname, match)
                if match:
                    drname = 'dr'
                    if pdgid:
                        drname = 'dr_{pdgid}'.format(pdgid=pdgid)
                    dr = deltaR(ptc, match)
                    setattr(ptc, drname, dr)
