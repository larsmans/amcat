import os, sys, toolkit, base64, odict, collections, re

def printError(name, msg):
    toolkit.warn(msg)

class Node(object):
    def __init__(self, id, label=None, weight=1, rank=None):
        self.id = id
        self.attrs = {}
        self.style = {}
        self.label = label
        self.weight = weight
        self.rank = rank
    def __str__(self):
        return "[Node %s]" % self.id

class Edge(object):
    def __init__(self, subj, obj, label=None, weight=1, sign=None, color=None):
        self.subj = subj
        self.obj = obj
        self.attrs = {}
        self.style = {}
        self.weight = weight
        self.label = label
        self.sign = sign
        self.color = color
    def __str__(self):
        return "[Edge %s-%s]" % (self.subj.id, self.obj.id)


MAIN_GRAPH = 1

class Graph(object):
    def __init__(self, digraph=True, label=None, theme=None):
        self.nodes = odict.OrderedDict() # id : Node
        self.edges = odict.OrderedDict() # subjNode, objNode : [Edge, ..]
        self.digraph = digraph
        self.label = label
        self.theme = theme or DotTheme()
        self.subgraphs = collections.defaultdict(list)

    def addNode(self, node, **kargs):
        if type(node) <> Node:
            node = Node(node, **kargs)
        self.nodes[node.id] = node
        return node

    def getNode(self, nodeid, create=True, **kargs):
        if nodeid in self.nodes:
            return self.nodes[nodeid]
        if create:
            return self.addNode(nodeid, **kargs)

    def addEdge(self, subj, obj, graph=None, **kargs):
        if type(subj) <> Node: subj = self.getNode(subj)
        if type(obj) <> Node: obj = self.getNode(obj)
        edge = Edge(subj, obj, **kargs)
        if (subj, obj) not in self.edges: self.edges[subj, obj] = []
        self.edges[subj, obj].append(edge)
        self.subgraphs[graph].append(edge)
        return edge

    def addLabel(self, label):
        self.label = label

    def getDot(self):
        entries = []
        #for node in self.nodes.values():
        #    entries.append(self.theme.getNodeDot(node, self))
        for i, subgraph in enumerate(self.subgraphs):
            if subgraph: entries.append('subgraph cluster_%i {\nlabel="%s"' % (i, subgraph))
            n = set()
            for edge in self.subgraphs[subgraph]:
                entries.append(self.theme.getEdgeDot(edge, self, subgraph))
                n.add(edge.subj)
                n.add(edge.obj)
            for node in n:
                entries.append(self.theme.getNodeDot(node, self, subgraph))
            if subgraph: entries.append("}")
        graphtype = "digraph" if self.digraph else "graph"
        header = self.theme.getGraphHeader(self)
        return "%s G {%s\n%s\n}" % (graphtype, header, "\n".join(e for e in entries if e))

    def getEdgesFrom(self, node):
        for (subj, obj), edges in self.edges.iteritems():
            if subj == node:
                for edge in edges:
                    yield edge
    def getEdgesTo(self, node):
        for (subj, obj), edges in self.edges.iteritems():
            if obj == node:
                for edge in edges:
                    yield edge
                        
        

    def getImage(self, *args, **kargs):
        return dot2img(self.getDot(), *args, **kargs)
    def getHTMLObject(self, *args, **kargs):
        return dot2object(self.getDot(), *args, **kargs)
    def getHTMLDoc(self):
        return '<html><body><p>%s</p><pre>%s</pre></body></html>' % (self.getHTMLObject(), self.getDot())
    def getHTMLSVG(self, *args, **kargs):
        kargs['format']='svg'
        svg = self.getImage(*args, **kargs)
        svg = re.match('.*?(<svg.*</svg>)', svg, re.DOTALL).group(1)
        return svg
    
    def normalizeWeights(self):
        wmin, wmax = 1, 10
        max, min = None, None
        for edges in self.edges.values():
            for edge in edges:
                w = float(edge.weight)
                if max is None or w > max: max = w
                if min is None or w < min: min = w
        if max <> min:
            self.theme.scale = (wmax - wmin) / (max - min)
            self.theme.base = wmin - (min*self.theme.scale)

class DotTheme(object):
    def __init__(self, edgelabels=True, shape="ellipse", isolated=False, edgefont="Helvetica", nodefont="Helvetica",header="", scale=1, base=0):
        self.edgelabels = edgelabels
        self.shape = shape
        self.isolated=  isolated
        self.nodefont = nodefont
        self.edgefont = edgefont
        self.header = header
        self.scale = scale
        self.graphattrs = {"center" : "true", "size" : "7.5,10"}
        self.base = base
    def getEdgeDot(self, edge, graph, subgraph):
        style = dict(edge.style)
        attrs = dict(edge.attrs)
        if edge.color is not None:
            hsb = edge.color
        else:
            hsb = self.getEdgeColor(edge, graph)
        if hsb: attrs['color'] = "%1.4f,%1.4f,%1.4f" % hsb
        w = self.getEdgeWidth(edge, graph)
        if w: style['setlinewidth'] = "%1.3f" % w
        l = self.getEdgeLabel(edge, graph)
        if l: attrs['label'] = l
        l = self.getEdgeLen(edge, graph)
        if l: attrs['len'] = l 
        a = dotattrs(attrs, style)
        c = self.getConnector(edge, graph)
        return '%s %s %s [%s];' % (self.getNodeID(edge.subj, graph, subgraph), c, self.getNodeID(edge.obj, graph, subgraph), a)
    def getEdgeWeight(self, edge, graph):
        return edge.weight * self.scale
    def getEdgeColor(self, edge, graph):
        if edge.sign:
            return (.833-.167*edge.sign,1,.5)
        return None
    def getEdgeWidth(self, edge, graph):
        return 1 + float(self.getEdgeWeight(edge, graph)) * .3333
    def getEdgeLen(self, edge, graph):
        return 1
    def getEdgeLabel(self, edge, graph):
        if self.edgelabels:
            return edge.label
    def getConnector(self, edge, graph):
        return graph.digraph and "->" or "--"

    def getNodeDot(self, node, graph, subgraph):
        if not (self.isolated or list(graph.getEdgesFrom(node)) or list(graph.getEdgesTo(node))):
            return ""
        style = dict(node.style)
        attrs = dict(node.attrs)
        hsb = self.getNodeFontColor(node, graph)
        if hsb: attrs['fontcolor'] = "%1.4f,%1.4f,%1.4f" % hsb
        f = self.getNodeFontsize(node, graph)
        if f: attrs['fontsize'] = f
        f = self.getNodeFontname(node, graph)
        if f: attrs['fontname'] = f
        s = self.getNodeShape(node, graph)
        if s: attrs['shape'] = s
        attrs['label'] = node.id
        a = dotattrs(attrs, style)
        return '%s [%s];' % (self.getNodeID(node, graph, subgraph), a)
    def getNodeID(self, node, graph, subgraph=None):
        if subgraph:
            return '"%s %s"' % (node.id, subgraph)
        return '"%s"' % node.id
    def getNodeShape(self, node, graph):
        return None
    def getNodeFontColor(self, node, graph):
        return None
    def getNodeFontsize(self, node, graph):
        return None
    def getNodeFontname(self, node, graph):
        return None
    def getNodeWeight(self, node, graph):
        return self.scale * node.weight + self.base
    def getGraphHeader(self, graph):
        header = ""
        a = self.getGraphAttrs(graph)
        if a: header += "graph [%s];\n" % dotattrs(a, None)
        a = self.getEdgeDefaultAttrs(graph)
        if a: header += "edge [%s];\n" % dotattrs(a, None)
        a = self.getNodeDefaultAttrs(graph)
        if a: header += "node [%s];\n" % dotattrs(a, None)
        if self.header: header += self.header
        return header
    def getGraphAttrs(self, graph):
        a = dict(self.graphattrs.items())
        if graph.label: a['label'] = graph.label
        return a
    def getEdgeDefaultAttrs(self, graph):
        a = dict(fontname=self.edgefont)
        return a
    def getNodeDefaultAttrs(self, graph):
        a = dict(fontname=self.nodefont,shape=self.shape)
        return a
        
    
    


def dotattrs(attrs, style):
    if style:
        attrs['style'] = ",".join("%s(%s)" % i for i in style.items())
    return ",".join('%s="%s"' % i for i in attrs.items())



HEADER_SMALL = "node [fontsize=10,height=.1]; graph [ranksep=.25]; edge [fontsize=10];"

def dot2img(dot, format="jpg", errListener = printError, layout="dot"):
    cmd = 'dot -T%s -K%s' % (format, layout)
    img, err = toolkit.execute(cmd, dot, listener=errListener)
    return img

def dot2object(dot,*args,**kargs):
    kargs['format'] = 'png'
    png = dot2img(dot, *args, **kargs)
    return toolkit.htmlImageObject(png)


if __name__ == '__main__':
    g = Graph()

    g.addEdge("a", "b", label="+1")
    g.addEdge("a", "c").label = "-1"
    n = Node("d", "dirk")
    g.addNode(n)
    g.addEdge(n, "b")
    g.getNode("b", create=False).label="boer"

    print g.getImage(format="png")
    
    #print dot2img(dot)
