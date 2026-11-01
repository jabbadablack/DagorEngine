// Copyright (C) Gaijin Games KFT. All rights reserved.
#include "brushDocument.h"
#include <ioSys/dag_dataBlock.h>
#include <cmath>
#include <iomanip>
#include <locale>
#include <sstream>
#include <stdexcept>

namespace csg
{
namespace
{
// BLK real/Point3 values are floats. Decimal strings preserve the authoring
// doubles exactly across saves, including at large world coordinates.
std::string number(double d)
{
  std::ostringstream s; s.imbue(std::locale::classic()); s<<std::setprecision(17)<<d; return s.str();
}
double readNumber(const DataBlock &b,const char *key,double fallback)
{
  const char *text=b.getStr(key,nullptr); if (!text) return fallback;
  std::istringstream s(text); s.imbue(std::locale::classic()); double d;
  if (!(s>>d) || !std::isfinite(d)) throw std::runtime_error("Invalid CSG numeric value");
  s>>std::ws; if (!s.eof()) throw std::runtime_error("Trailing data in CSG numeric value"); return d;
}
void saveVec(DataBlock &b,const char *key,Vec v)
{
  std::string text=number(v.x)+" "+number(v.y)+" "+number(v.z); b.setStr(key,text.c_str());
}
Vec readVec(const DataBlock &b,const char *key,Vec fallback={})
{
  const char *text=b.getStr(key,nullptr); if (!text) return fallback;
  Vec v; std::istringstream s(text); s.imbue(std::locale::classic());
  if (!(s>>v.x>>v.y>>v.z) || !finite(v)) throw std::runtime_error("Invalid CSG vector");
  s>>std::ws; if (!s.eof()) throw std::runtime_error("Trailing data in CSG vector"); return v;
}
void saveSurface(const Surface &s,DataBlock &b)
{
  b.setStr("material",s.material.c_str()); saveVec(b,"u",s.u); saveVec(b,"v",s.v);
  b.setStr("scaleU",number(s.scaleU).c_str()); b.setStr("scaleV",number(s.scaleV).c_str());
  b.setStr("offsetU",number(s.offsetU).c_str()); b.setStr("offsetV",number(s.offsetV).c_str());
  b.setStr("rotation",number(s.rotation).c_str()); b.setBool("worldLocked",s.worldLocked); b.setInt("smoothing",s.smoothing);
}
Surface readSurface(const DataBlock &b)
{
  Surface s; s.material=b.getStr("material",""); s.u=readVec(b,"u",s.u); s.v=readVec(b,"v",s.v);
  s.scaleU=readNumber(b,"scaleU",1); s.scaleV=readNumber(b,"scaleV",1);
  s.offsetU=readNumber(b,"offsetU",0); s.offsetV=readNumber(b,"offsetV",0); s.rotation=readNumber(b,"rotation",0);
  s.worldLocked=b.getBool("worldLocked",false); s.smoothing=b.getInt("smoothing",0); return s;
}
void saveNode(const Node &n,DataBlock &b)
{
  b.setInt64("id",n.id); b.setStr("name",n.name.c_str()); b.setInt("operation",int(n.operation)); b.setBool("visible",n.visible);
  const char *keys[]={"axisX","axisY","axisZ","origin"};
  for (unsigned i=0;i<4;++i) saveVec(b,keys[i],n.transform.column[i]);
  b.setBool("overrideCutSurface",n.overrideCutSurface); if (n.overrideCutSurface) saveSurface(n.cutSurface,*b.addNewBlock("cutSurface"));
  auto &mesh=*b.addNewBlock("brush");
  for (auto p:n.brush.vertices) { auto &v=*mesh.addNewBlock("vertex"); saveVec(v,"position",p); }
  for (const auto &f:n.brush.faces)
  {
    auto &face=*mesh.addNewBlock("face"); face.setInt64("id",f.id); face.setInt64("sourceBrush",f.sourceBrush);
    for (auto i:f.vertices) face.addInt("index",i);
    saveSurface(f.surface,*face.addNewBlock("surface"));
  }
  for (const auto &c:n.children) saveNode(c,*b.addNewBlock("node"));
}
Node readNode(const DataBlock &b,unsigned depth,size_t &budget)
{
  if (depth>128 || budget++>100000) throw std::runtime_error("CSG document exceeds hierarchy limits");
  Node n; n.id=b.getInt64("id",0); n.name=b.getStr("name","");
  int op=b.getInt("operation",0); if (op<0 || op>2) throw std::runtime_error("Unknown CSG boolean operation");
  n.operation=Operation(op); n.visible=b.getBool("visible",true);
  const char *keys[]={"axisX","axisY","axisZ","origin"};
  for (unsigned i=0;i<4;++i) n.transform.column[i]=readVec(b,keys[i],n.transform.column[i]);
  n.overrideCutSurface=b.getBool("overrideCutSurface",false); n.cutSurface=readSurface(*b.getBlockByNameEx("cutSurface"));
  const auto &mesh=*b.getBlockByNameEx("brush");
  for (int i=0;i<mesh.blockCount();++i)
  {
    const auto &part=*mesh.getBlock(i);
    if (strcmp(part.getBlockName(),"vertex")==0) n.brush.vertices.push_back(readVec(part,"position"));
    else if (strcmp(part.getBlockName(),"face")==0)
    {
      Face f; f.id=part.getInt64("id",0); f.sourceBrush=part.getInt64("sourceBrush",0);
      for (int j=0;j<part.paramCount();++j) if (strcmp(part.getParamName(j),"index")==0) f.vertices.push_back(part.getInt(j));
      f.surface=readSurface(*part.getBlockByNameEx("surface")); n.brush.faces.push_back(std::move(f));
    }
  }
  for (int i=0;i<b.blockCount();++i) if (strcmp(b.getBlock(i)->getBlockName(),"node")==0) n.children.push_back(readNode(*b.getBlock(i),depth+1,budget));
  return n;
}
}
void saveDocument(const Document &doc,DataBlock &b)
{
  b.clearData(); b.setInt("version",Document::VERSION); b.setInt64("nextId",doc.nextId); saveNode(doc.root,*b.addNewBlock("root"));
}
bool loadDocument(const DataBlock &b,Document &doc,Diagnostics &errors)
{
  try
  {
    if (b.getInt("version",0)!=Document::VERSION) throw std::runtime_error("Unsupported CSG document version; source data retained");
    Document candidate; candidate.nextId=b.getInt64("nextId",0); size_t budget=0;
    const DataBlock *root=b.getBlockByName("root"); if (!root) throw std::runtime_error("Missing CSG root");
    candidate.root=readNode(*root,0,budget);
    // Loading is transactional. Evaluation also checks stable identities.
    Evaluator validator; Result r=validator.evaluate(candidate);
    if (!r.success) { errors=std::move(r.diagnostics); return false; }
    doc=std::move(candidate); return true;
  }
  catch(const std::exception &e) { errors.push_back({Code::InvalidDocument,0,0,e.what()}); return false; }
}
}
