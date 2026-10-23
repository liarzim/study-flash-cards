"""Draw chemical structures from SMILES as textbook-style SVGs (RDKit).
Atoms with atom-map number 1 (e.g. [CH2:1]) are highlighted in gray."""
import json, math, sys
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Geometry import Point3D
rdDepictor.SetPreferCoordGen(True)
def orient(m):
  # find alpha carbon: C bonded to N and to a carboxylate C
  patt=Chem.MolFromSmarts('[N;X4,X3;+1,+0]-[CX4]-[CX3](=O)[O-,OH]')
  hit=m.GetSubstructMatch(patt)
  if not hit: return
  n,ca,cc=hit[0],hit[1],hit[2]
  conf=m.GetConformer(); P=lambda i: conf.GetAtomPosition(i)
  ang=math.atan2(P(cc).y-P(n).y, P(cc).x-P(n).x)
  c,s=math.cos(-ang),math.sin(-ang)
  for i in range(m.GetNumAtoms()):
    p=P(i); conf.SetAtomPosition(i,Point3D(p.x*c-p.y*s, p.x*s+p.y*c,0))
  side=[a.GetIdx() for a in m.GetAtoms() if a.GetAtomMapNum()==1]
  if side:
    cy=sum(P(i).y for i in side)/len(side)
    if cy<P(ca).y:
      for i in range(m.GetNumAtoms()):
        p=P(i); conf.SetAtomPosition(i,Point3D(p.x,-p.y,0))
def svg(smiles):
  m=Chem.MolFromSmiles(smiles)
  hl=[a.GetIdx() for a in m.GetAtoms() if a.GetAtomMapNum()==1]
  hb=[b.GetIdx() for b in m.GetBonds() if b.GetBeginAtomIdx() in hl and b.GetEndAtomIdx() in hl]
  rdDepictor.Compute2DCoords(m); orient(m)
  for a in m.GetAtoms(): a.SetAtomMapNum(0)
  d=rdMolDraw2D.MolDraw2DSVG(-1,-1)
  o=d.drawOptions(); o.fixedBondLength=38; o.bondLineWidth=2; o.padding=0.08; o.addStereoAnnotation=False
  o.highlightRadius=0.42; o.fillHighlights=True; o.continuousHighlight=True; o.clearBackground=False
  o.setHighlightColour((0.85,0.87,0.89,1)); o.minFontSize=13; o.maxFontSize=18; o.multipleBondOffset=0.18
  o.updateAtomPalette({7:(0.11,0.37,0.55),8:(0.76,0.17,0.15),16:(0.60,0.42,0.0)})
  rdMolDraw2D.PrepareAndDrawMolecule(d,m,highlightAtoms=hl,highlightBonds=hb)
  d.FinishDrawing(); return d.GetDrawingText()
def svg_file(smiles, path):
  import re
  out=re.sub(r"<\?xml[^>]*\?>\s*","",svg(smiles)).replace('<!-- END OF HEADER -->','')
  with open(path,'w',encoding='utf-8') as f: f.write(out)

if __name__=='__main__':
  # usage: python tools/render_mol.py [topic-id]   (default: amino-acids)
  import os, re
  tid=sys.argv[1] if len(sys.argv)>1 else 'amino-acids'
  base=os.path.join(os.path.dirname(__file__),'..','public','topics',tid)
  topic=json.load(open(os.path.join(base,'topic.json'),encoding='utf-8'))
  for c in topic['cards']:
    if not c.get('smiles'): continue
    svg_file(c['smiles'], os.path.join(base,c['image']))
    print('drew',c['image'])
