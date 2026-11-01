// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <libTools/CSG/brush.h>
#include <chrono>
#include <iostream>

// Geometry-only lower bound. Passing this test DOES NOT pass the release gate:
// the release gate also includes UV atlasing, collision and viewport publication.
int main()
{
  csg::Document doc; doc.assignIds(doc.root);
  for (unsigned i=0;i<1000;++i)
  {
    csg::Node n; n.brush=csg::box({1,1,1});
    n.transform.column[3]={double(i%40)*4,0,double(i/40)*4};
    doc.assignIds(n); doc.root.children.push_back(std::move(n));
  }
  csg::Evaluator evaluator;
  if (!evaluator.evaluate(doc).success) return 2;
  double worst=0;
  for (unsigned frame=0;frame<10;++frame)
  {
    doc.root.children[500].transform.column[3].y=frame*0.01;
    auto start=std::chrono::steady_clock::now(); auto result=evaluator.evaluate(doc);
    if (!result.success) return 2;
    double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    worst=std::max(worst,ms); std::cout<<"geometry-only update "<<frame<<": "<<ms<<" ms\n";
  }
  std::cout<<"Geometry-only worst: "<<worst<<" ms; full release gate NOT evaluated\n";
  return worst<=33 ? 0:1;
}
