import math
from heppy.particles.tlv.particle import Particle as BaseParticle
from heppy.utils.deltar import deltaR
from heppy.papas.data.idcoder import IdCoder
from heppy.configuration import Collider
from ROOT import TVector3

#add angular size needs to be fixed since at the moment the angluar size is set by the first elementsize
#in a merged cluster. If the merged cluster is formed in a different order then the angular size will be different

class PFObject(object):
    '''Base class for all particle flow objects (tracks, clusters, etc).
    Particle flow objects of different types can be linked together
    forming graphs called "blocks".
    All PFObjects have a unique identifier which encodes information about the object type, subtype and an associated value such 
    as energy or pt. See Identifier class for more details. 
    attributes:
    linked : list of PFObjects linked to this one
    locked : already used in the particle flow algorithm
    block_label : label of the block the PFObject belongs to. The block label is a unique identifier for the block.
    '''


    def __init__(self, pfobjecttype, index, subtype='u', identifiervalue = 0.0):
        '''@param pfobjecttype: type of the object to be created (used in Identifier class) eg Identifier.PFOBJECTTYPE.ECALCLUSTER
           @param subtype: Identifier subtype, eg 'm' for merged
           @param identifiervalue: The value to be encoded into the Identifier eg energy or pt
    '''
        super(PFObject, self).__init__()
        self.linked = []
        self.locked = False
        self.block_label = None
        self.uniqueid=IdCoder.make_id(pfobjecttype, index, subtype, identifiervalue)

    def accept(self, visitor):
        '''Called by visitors, such as FloodFill. See pfalgo.floodfill'''
        notseen = visitor.visit(self)
        if notseen:
            for elem in self.linked:
                elem.accept(visitor)

    def __repr__(self):
        return str(self)

    def info(self):
        return ""

    def __str__(self):
        return '{classname}: {pretty:6}:{uid}: {info}'.format(
            classname=self.__class__.__name__,
            pretty=IdCoder.pretty(self.uniqueid),
            uid=self.uniqueid,
            info=self.info())


class Cluster(PFObject):
    '''
    TODO:
    - not sure  max_energy plays well with SmearedClusters
    - investigate the possibility to have only one class.
     so: put mother in Cluster
     define the identifier outside?
    or stay as it is, but do not do any work in the child SmearedCluster and MergedCluster classes
    '''

    #TODO: not sure this plays well with SmearedClusters
    max_energy = 0.

    def __init__(self, energy, position, size_m, layer='ecal_in',index=0, particle=None, identifiervalue=None):
        if not hasattr(self, 'subtype'):
            self.subtype = 't'
        #may be better to have one PFOBJECTTYPE.CLUSTER type and also use the layer...
        if identifiervalue== None:
            identifiervalue = max(energy, 0.)
        if layer == 'ecal_in':
            super(Cluster, self).__init__(IdCoder.PFOBJECTTYPE.ECALCLUSTER, index, self.subtype, identifiervalue)
        elif layer == 'hcal_in':
            super(Cluster, self).__init__(IdCoder.PFOBJECTTYPE.HCALCLUSTER, index, self.subtype, identifiervalue)
        else :
            assert (False)
        self.position = position
        self.set_energy(energy)
        self.set_size(float(size_m))
        self.layer = layer
        self.particle = particle
        self.subclusters = [self]
        # self.absorbed = []

    def set_size(self, value):
        '''Set cluster radius in cm.'''
        self._size = value
        try:
            self._angularsize = math.atan(self._size / self.position.Mag())
        except:
            import pdb; pdb.set_trace()

    def size(self):
        '''Returns the cluster radius in cm.
        
        Only valid for non-merged clusters.
        '''
        return self._size

    def angular_size(self):
        '''Returns the cluster radius in radians.
        
        Only valid for non-merged clusters.
        '''
        return self._angularsize

    def is_inside_clusters(self, other):
        '''TODO: no need for two versions of this method, see below.
        one should have a single overlap method that always works, whether or not there are any
        subclusters.
        '''
        #see if two clusters overlap (allowing for merged clusters which contain subclusters)
        #we have a link if any of the subclusters overlap
        #the distance is the distance betewen the weighted centres of each (merged) cluster

        dist = deltaR(self.position.Theta(),
                      self.position.Phi(),
                      other.position.Theta(),
                      other.position.Phi())

        for c in self.subclusters:
            for o in  other.subclusters:
                is_link, innerdist = c.is_inside_cluster(o)
                if is_link:
                    return True, dist
        return False, dist


    def is_inside_cluster(self, other):
        '''TODO change name to "overlaps" ? '''
        #now we have original unmerged clusters so we can compare directly to see if they overlap
        dR = deltaR(self.position.Theta(),
                    self.position.Phi(),
                    other.position.Theta(),
                    other.position.Phi())
        link_ok = dR < self.angular_size() + other.angular_size()
        return link_ok, dR


    def is_inside(self, point):
        """check if the point lies within the "size" circle of each of the subclusters"""
        subdist = []
        for subc in self.subclusters:
            dist = (subc.position - point).Mag()
            if dist < subc.size():
                subdist.append(dist)
        if len(subdist):
            return True, min(subdist)

        subdists = [(subc.position - point).Mag() for subc in self.subclusters]
        dist = min(subdists)
        return False, dist
    

    def __iadd__(self, other):
        if other.layer != self.layer:
            raise ValueError('can only add a cluster from the same layer')
        position = self.position * self.energy + other.position * other.energy
        energy = self.energy + other.energy
        denom = 1/energy
        position *= denom
        self.position = position
        self.energy = energy
        assert (len(other.subclusters) == 1)
        self.subclusters.extend(other.subclusters)

        #todo recalculate the angular size
        return self

    def set_energy(self, energy):
        energy = float(energy)
        self.energy = energy
        if energy > self.__class__.max_energy:
            self.__class__.max_energy = energy
        self.pt = energy * self.position.Unit().Perp()

    # fancy but I prefer the other solution
    # def __setattr__(self, name, value):
    #     if name == 'energy':
    #         self.pt = value * self.position.Unit().Perp()
    #     self.__dict__[name] = value
    def info(self):
        subclusterstr = str('sub(')
        for s in self.subclusters:
            subclusterstr += str('{:}, '.format(IdCoder.pretty(s.uniqueid)))
        subclusterstr += ")"
        return '{energy:7.2f} {theta:5.2f} {phi:5.2f} {sub}'.format(
            energy=self.energy,
            theta=math.pi/2. - self.position.Theta(),
            phi=self.position.Phi(),
            sub=subclusterstr
        )

    def short_info(self):
        return '{e:.1f}'.format(
            e = self.energy,
        )

class SmearedCluster(Cluster):
    def __init__(self, mother, *args, **kwargs):
        self.mother = mother
        self.subtype = 's'
        super(SmearedCluster, self).__init__(*args, **kwargs)

class MergedCluster(Cluster):
    '''The MergedCluster is used to hold a cluster that has been merged from other clusters '''

    def __init__(self, clusters, index=0, identifiervalue=None):
        '''identifiervalue will be used to help create the merged cluster unique identifier'''
        position = None
        energy = 0.
        firstcluster = None
        for cluster in clusters:
            if not firstcluster:
                firstcluster = cluster
                position = cluster.position * cluster.energy
                energy = cluster.energy
            else:
                position += cluster.position * cluster.energy
                energy += cluster.energy
        position *= (1./energy)           
        self.subtype = 'm'
        super(MergedCluster, self).__init__(energy, position, firstcluster._size, firstcluster.layer, index, identifiervalue=energy)
        self.subclusters = clusters 

    def __iadd__(self, other):
        '''TODO: why not using iadd from base class'''
        if other.layer != self.layer:
            raise ValueError('can only add a cluster from the same layer')
        position = self.position * self.energy + other.position * other.energy
        energy = self.energy + other.energy
        denom = 1/energy
        position *= denom
        self.position = position
        self.energy = energy
        self.subclusters.extend([other])

        return self

class Track(PFObject):
    '''Determines the trajectory in space and time of a particle (charged or neutral).
    attributes:
    - p3 : momentum in 3D space (px, py, pz)
    - charge : particle charge
    - path : contains the trajectory parameters and points
    '''
    
    def __init__(self, p3, charge, path, index=0, particle=None, subtype='t'):
        if not hasattr(self, 'subtype'):
            self.subtype = subtype        
        super(Track, self).__init__(IdCoder.PFOBJECTTYPE.TRACK, index, self.subtype, p3.Mag())

        self._p3 = p3
        self.charge = charge
        self.path = path
        self.particle = particle
        self.layer = 'tracker'

    def p3(self):
        return self._p3

    def theta(self):
        return math.pi/2. - self._p3.Theta()

    def info(self):
        return '{p:7.2f} {pt:7.2f} {theta:5.2f} {phi:5.2f}'.format(
            pt=self._p3.Perp(),
            p=self._p3.Mag(),
            theta=self.theta(),
            phi=self._p3.Phi()
        )

    def short_info(self):
        return '{e:.1f}'.format(
            e = self.energy,
        )     

    
class SmearedTrack(Track):
    
    def __init__(self, mother, *args, **kwargs):
        self.mother = mother
        self.path = mother.path  # pass this to init below?
        self.subtype = 's'
        super(SmearedTrack, self).__init__(*args, **kwargs)


class Particle(BaseParticle):
    def __init__(self, tlv, vertex, charge, pdgid):
        super(Particle, self).__init__(pdgid, charge, tlv)
    #allow the value used in the particle unique id to depend on the collider type
        self.idvalue = 0.
        if Collider.BEAMS == 'ee':
            self.idvalue=self.e()
        else:
            self.idvalue=self.pt()
        self.vertex = vertex
        self.path = None
        self.clusters = dict()
        self.track = None # to match cpp 
        self.clusters_smeared = dict()
        self.track_smeared = None

    def __getattr__(self, name):
        if name == 'points':
            # if self.path is None:
            #     import pdb; pdb.set_trace()
            return self.path.points
        else:
            raise AttributeError

    def is_em(self):
        kind = abs(self.pdgid())
        return kind == 11 or kind == 22

    def set_path(self, path, option=None):
        if option == 'w' or self.path is None:
            self.path = path
            if self.q(): # todo check this is OK for multiple scattering?
                if self.track:
                    self.track.path = self.path
                if self.track_smeared:
                    self.track_smeared.path = self.path #is this really what we want
    
    def set_track(self, track):
        self.track = track 
        self.path = track.path;

    def short_info(self):
        tmp = '{pdgid:} ({e:.1f})'
        #needed for now to get match with C++
        pid=self.pdgid()
        if self.q() == 0 and pid < 0:
            pid = -pid        
        
        return tmp.format(
            pdgid =pid,
            e = self.e()
        )

    def  dagid_str(self):
        if self.dagid() != None:
            return IdCoder.id_str(self.dagid())
        return ""


if __name__ == '__main__':
    from ROOT import TVector3
    cluster = Cluster(10., TVector3(1, 0, 0), 1)  #alice made this use default layer
    print cluster.pt
    cluster.set_energy(5.)
    print cluster.pt
