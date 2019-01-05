'''Filter events based on object counting. (deprecated, see EventFilter)'''


from heppy.framework.analyzer import Analyzer

class Counter(Analyzer):
    '''Counts the number of objects in the input_objects collection
    and skip the event if this number is strictly inferior to min_number

    Example: 

    from heppy.analyzers.Counter import Counter
    gen_counter = cfg.Analyzer(
       Counter,
       input_objects = 'gen_particles_stable',
       min_number = 1
    )

    * input_objects : the input collection 

    * min_number : the minimum amount of object in input_object to not skip the event
    '''

    def process(self, event):
        '''event should contain:
        
        * self.cfg_ana.input_objects:
             the list of input_objects to be counted, 
             with the name specified in self.cfg_ana
        '''
        input_collection = getattr(event, self.cfg_ana.input_objects)
        return len(input_collection) >= self.cfg_ana.min_number
