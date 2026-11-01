// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <libTools/CSG/brush.h>
#include <cmath>
#include <iostream>
#include <map>
#include <stdexcept>

static void require(bool test,const char *message) { if (!test) throw std::runtime_error(message); }
static void near(double a,double b,const char *message) { require(std::abs(a-b)<1e-7,message); }
int main()
{
  try
  {
    csg::Diagnostics errors;
    auto a=csg::box({2,2,2}); require(csg::validate(a,errors,0,true),"box validity"); near(csg::volume(a),8,"box volume");
    auto ramp=csg::ramp({2,3,4}); require(csg::validate(ramp,errors,0,true),"ramp validity"); near(csg::volume(ramp),12,"ramp volume");
    require(csg::validate(csg::cylinder(1,2,16),errors,0,true),"cylinder validity");
    auto b=csg::box({1,1,1});
    auto cut=csg::booleanOperation(a,b,csg::Operation::Subtract); require(cut.success,"contained subtraction"); near(csg::volume(*cut.mesh),7,"hollow solid volume");
    csg::Mesh publishedCut; require(csg::triangulateForPublication(*cut.mesh,publishedCut,errors),"triangulate cavity for publication");
    near(csg::volume(publishedCut),7,"publication preserves cavity volume");
    for(const auto &face:publishedCut.faces) require(face.vertices.size()==3,"publication produces triangles");
    auto same=csg::booleanOperation(a,a,csg::Operation::Subtract); require(same.success && same.mesh->faces.empty(),"identical subtraction");
    auto merged=csg::booleanOperation(a,a,csg::Operation::Union); require(merged.success,"coincident union"); near(csg::volume(*merged.mesh),8,"coincident volume");
    csg::Transform tm; tm.column[3]={2,2,0};
    auto touching=csg::booleanOperation(a,csg::transformed(a,tm),csg::Operation::Union);
    require(touching.success && touching.mesh->vertices.size()==16,"edge contact must not weld");
    tm.column[3]={2,2,2}; touching=csg::booleanOperation(a,csg::transformed(a,tm),csg::Operation::Union);
    require(touching.success && touching.mesh->vertices.size()==16,"point contact must not weld");
    csg::Transform step0,step1; step0.column[3]={6,0.1,0}; step1.column[3]={6,0.1+0.2,0.4};
    auto stair=csg::box({2,0.2,0.4});
    auto stairContact=csg::booleanOperation(csg::transformed(stair,step0),csg::transformed(stair,step1),csg::Operation::Union);
    require(stairContact.success && stairContact.mesh->vertices.size()==16,"decimal stair edge contact preserves components");
    tm.column[3]={2,0,0}; auto faceContact=csg::booleanOperation(a,csg::transformed(a,tm),csg::Operation::Union);
    require(faceContact.success,"face contact union"); near(csg::volume(*faceContact.mesh),16,"face contact volume");
    tm.column[3]={1000,0,1000}; auto far=csg::transformed(a,tm); auto thin=csg::transformed(csg::box({0.01,3,3}),tm);
    auto precise=csg::booleanOperation(far,thin,csg::Operation::Subtract); require(precise.success,"centimeter cut at kilometer offset"); near(csg::volume(*precise.mesh),7.96,"centimeter cut volume");
    csg::Transform almostParallel; almostParallel.column[3]={1000,0,1000};
    almostParallel.column[0]={std::cos(1e-6),std::sin(1e-6),0};
    almostParallel.column[1]={-std::sin(1e-6),std::cos(1e-6),0};
    auto nearParallel=csg::booleanOperation(far,csg::transformed(csg::box({0.01,3,3}),almostParallel),csg::Operation::Subtract);
    require(nearParallel.success,"near-parallel centimeter cut at kilometer offset");
    near(csg::volume(*nearParallel.mesh),7.96,"near-parallel cut volume");
    csg::Transform distant; distant.column[3]={10,0,0};
    auto disjointIntersection=csg::booleanOperation(a,csg::transformed(a,distant),csg::Operation::Intersect);
    require(disjointIntersection.success && disjointIntersection.mesh->faces.empty(),"disjoint intersection");
    tm.column[0]={-1,0,0}; require(csg::validate(csg::transformed(a,tm),errors,0,true),"mirrored brush");
    auto original=a; require(!csg::moveVertices(a,{0},{3,3,3},errors),"reject concave edit"); near(csg::volume(a),csg::volume(original),"rejected edit transactional");
    errors.clear(); auto clipped=a; require(csg::clip(clipped,{1,0,0},0,99,{},errors),"clip box"); near(csg::volume(clipped),4,"clip volume");
    auto beveled=a; require(csg::bevel(beveled,{0},0.1,100,errors),"bevel vertex"); require(csg::volume(beveled)<8,"bevel removes volume");
    auto invalidBevel=a; require(!csg::bevel(invalidBevel,{0,6},0.1,101,errors),"reject diagonal bevel selection");
    near(csg::volume(invalidBevel),8,"invalid bevel preserves brush");
    csg::Mesh extrusion; require(csg::extrudeFace(a,0,1,extrusion,errors),"face extrusion"); near(csg::volume(extrusion),4,"extrusion volume");
    std::vector<csg::Mesh> prisms;
    require(csg::extrudeOutline({{0,0,0},{2,0,0},{2,1,0},{1,1,0},{1,2,0},{0,2,0}},{0,0,2},prisms,errors),"concave outline extrusion");
    double v=0; for (auto &p:prisms) v+=csg::volume(p); near(v,6,"outline prism volume");
    require(!csg::extrudeOutline({{0,0,0},{2,2,0},{0,2,0},{2,0,0}},{0,0,1},prisms,errors),"reject crossed outline");
    csg::Document document; document.assignIds(document.root);
    csg::Node solid; solid.brush=a; document.assignIds(solid); document.root.children.push_back(solid);
    csg::Node cutter; cutter.brush=b; cutter.operation=csg::Operation::Subtract; document.assignIds(cutter); document.root.children.push_back(cutter);
    csg::Evaluator evaluator; auto first=evaluator.evaluate(document); require(first.success,"document evaluation"); near(csg::volume(*first.mesh),7,"document volume");
    auto cached=evaluator.evaluate(document); require(cached.success && cached.booleanCalls==0 && cached.cacheHits==1,"unchanged document cached");
    document.root.children[1].transform.column[3]={0.25,0,0};
    auto incremental=evaluator.evaluate(document); csg::Evaluator full; auto rebuilt=full.evaluate(document);
    require(incremental.success && rebuilt.success && incremental.cacheHits>0,"incremental evaluation");
    near(csg::volume(*incremental.mesh),csg::volume(*rebuilt.mesh),"incremental/full equivalence");
    csg::Document nested; nested.assignIds(nested.root);
    csg::Node outer; outer.brush=csg::box({4,4,4}); nested.assignIds(outer); nested.root.children.push_back(outer);
    csg::Node group; group.operation=csg::Operation::Subtract;
    for(double x:{-0.5,0.5})
    {
      csg::Node child; child.brush=csg::box({2,2,2}); child.transform.column[3].x=x;
      for(auto &face:child.brush.faces) { face.surface.material="cutter"; face.surface.offsetU=0.375; }
      group.children.push_back(std::move(child));
    }
    csg::Node limit; limit.brush=csg::box({10,1,1}); limit.operation=csg::Operation::Intersect;
    for(auto &face:limit.brush.faces) { face.surface.material="cutter"; face.surface.offsetU=0.375; }
    group.children.push_back(limit); nested.assignIds(group); nested.root.children.push_back(group);
    csg::Evaluator nestedEvaluator; auto nestedResult=nestedEvaluator.evaluate(nested);
    require(nestedResult.success,"nested ordered union/intersection/subtraction"); near(csg::volume(*nestedResult.mesh),61,"nested volume");
    bool attributed=false;
    for(const auto &face:nestedResult.mesh->faces)
      if(face.surface.material=="cutter")
      {
        require(face.sourceBrush && face.id,"cut face source attribution");
        near(face.surface.offsetU,0.375,"cut mapping inheritance"); attributed=true;
      }
    require(attributed,"subtraction inherits cutter material");
    nested.root.children[1].children[0].transform.column[3].x=-0.4;
    auto nestedIncremental=nestedEvaluator.evaluate(nested); csg::Evaluator nestedFull;
    auto nestedRebuilt=nestedFull.evaluate(nested);
    require(nestedIncremental.success && nestedRebuilt.success,"nested local edit");
    near(csg::volume(*nestedIncremental.mesh),csg::volume(*nestedRebuilt.mesh),"nested incremental/full volume");
    auto differenceA=csg::booleanOperation(*nestedIncremental.mesh,*nestedRebuilt.mesh,csg::Operation::Subtract);
    auto differenceB=csg::booleanOperation(*nestedRebuilt.mesh,*nestedIncremental.mesh,csg::Operation::Subtract);
    require(differenceA.success && differenceB.success,"incremental/full symmetric difference");
    near(csg::volume(*differenceA.mesh)+csg::volume(*differenceB.mesh),0,"incremental/full occupied geometry");
    auto surfaceAreas=[](const csg::Mesh &mesh) {
      std::map<uint64_t,double> areas;
      for(const auto &face:mesh.faces)
      {
        csg::Node signature; auto f=face; f.vertices.clear(); signature.brush.faces.push_back(f);
        auto key=csg::fingerprint(signature);
        for(size_t i=1;i+1<face.vertices.size();++i)
          areas[key]+=0.5*csg::length(csg::cross(mesh.vertices[face.vertices[i]]-mesh.vertices[face.vertices[0]],
            mesh.vertices[face.vertices[i+1]]-mesh.vertices[face.vertices[0]]));
      }
      return areas;
    };
    auto areasA=surfaceAreas(*nestedIncremental.mesh),areasB=surfaceAreas(*nestedRebuilt.mesh);
    require(areasA.size()==areasB.size(),"incremental/full source surface identities");
    for(const auto &entry:areasA)
    { require(areasB.count(entry.first),"incremental/full surface mapping and materials"); near(entry.second,areasB.at(entry.first),"incremental/full attributed surface area"); }
    document.root.children[1].brush.vertices[0].x=std::nan(""); auto failed=evaluator.evaluate(document);
    require(!failed.success && evaluator.lastValid().mesh==incremental.mesh,"last valid result preserved");
    document.root.children[1].id=solid.id; require(!evaluator.evaluate(document).success,"duplicate identity rejected");
    csg::Surface surface; surface.rotation=37; surface.scaleU=2; surface.scaleV=3;
    a.faces[0].surface=surface; tm=csg::Transform{}; tm.column[3]={23,11,-4}; tm.column[0]={2,0,0};
    auto mapped=csg::transformed(a,tm); auto before=csg::textureCoordinates(surface,a.vertices[0]);
    auto after=csg::textureCoordinates(mapped.faces[0].surface,mapped.vertices[0]);
    near(before[0],after[0],"brush locked U"); near(before[1],after[1],"brush locked V");
    csg::Document overrideDocument; overrideDocument.assignIds(overrideDocument.root);
    csg::Node overrideOuter; overrideOuter.brush=csg::box({4,4,4}); overrideDocument.assignIds(overrideOuter);
    overrideDocument.root.children.push_back(overrideOuter);
    csg::Node overrideGroup; overrideGroup.operation=csg::Operation::Subtract; overrideGroup.overrideCutSurface=true;
    overrideGroup.cutSurface.material="override"; overrideGroup.cutSurface.rotation=37;
    overrideGroup.transform.column[3]={0.25,0.1,0};
    overrideGroup.transform.column[0]={std::cos(0.2),std::sin(0.2),0};
    overrideGroup.transform.column[1]={-std::sin(0.2),std::cos(0.2),0};
    csg::Node overrideBrush; overrideBrush.brush=csg::box({2,2,2}); overrideGroup.children.push_back(overrideBrush);
    overrideDocument.assignIds(overrideGroup); overrideDocument.root.children.push_back(overrideGroup);
    for(bool worldLocked:{false,true})
    {
      auto &group=overrideDocument.root.children[1]; group.cutSurface.worldLocked=worldLocked;
      csg::Evaluator overrideEvaluator; auto output=overrideEvaluator.evaluate(overrideDocument);
      require(output.success,"nested operation surface override evaluation");
      bool foundOverride=false;
      for(const auto &face:output.mesh->faces) if(face.surface.material=="override")
      {
        foundOverride=true;
        for(auto index:face.vertices)
        {
          auto p=output.mesh->vertices[index];
          auto expected=csg::textureCoordinates(group.cutSurface,worldLocked ? p:group.transform.inversePoint(p));
          auto actual=csg::textureCoordinates(face.surface,p);
          near(expected[0],actual[0],"group override locked U"); near(expected[1],actual[1],"group override locked V");
        }
      }
      require(foundOverride,"nested operation override material attribution");
    }
    csg::Document room; room.assignIds(room.root);
    auto roomBrush=[&](csg::Vec size,csg::Vec position,csg::Operation operation) {
      csg::Node n; n.brush=csg::box(size); n.transform.column[3]=position; n.operation=operation;
      room.assignIds(n); room.root.children.push_back(std::move(n));
    };
    roomBrush({8,4,8},{0,2,0},csg::Operation::Union);
    roomBrush({7.5,3.5,7.5},{0,2,0},csg::Operation::Subtract);
    roomBrush({1.2,2.3,1},{0,1.15,-4},csg::Operation::Subtract);
    for(int i=0;i<8;++i) roomBrush({2,0.2,0.4},{6,0.1+i*0.2,i*0.4},csg::Operation::Union);
    roomBrush({1,1,1},{1.5,1,5},csg::Operation::Union);
    roomBrush({2,2,2},{0,0,0},csg::Operation::Union);
    csg::Evaluator roomEvaluator; auto roomResult=roomEvaluator.evaluate(room);
    require(roomResult.success,"create box crossing hollow room floor");
    near(csg::volume(*roomResult.mesh),67.64,"room, doorway, stairs, comparison and floor-crossing box volume");
    auto beforeRepeats=room; auto repeated=room.root.children.back();
    for(int i=0;i<8;++i)
    {
      repeated.transform.column[3]=repeated.transform.column[3]+csg::Vec{0,double(0.2f),double(0.3f)};
      auto copy=repeated; room.assignIds(copy); room.root.children.push_back(copy);
    }
    auto repeatedResult=roomEvaluator.evaluate(room);
    if(!repeatedResult.success) for(const auto &error:repeatedResult.diagnostics) std::cerr<<error.message<<'\n';
    require(repeatedResult.success,"repeated overlapping boxes crossing room floor");
    csg::Mesh repeatedPublished; errors.clear();
    auto publicationOK=csg::triangulateForPublication(*repeatedResult.mesh,repeatedPublished,errors);
    if(!publicationOK) for(const auto &error:errors) std::cerr<<error.message<<'\n';
    require(publicationOK,"publish repeated overlapping boxes crossing room floor");
    near(csg::volume(repeatedPublished),csg::volume(*repeatedResult.mesh),"collinear boundary triangulation preserves volume");
    auto floatPublished=repeatedPublished; auto floatOrigin=floatPublished.vertices.front();
    for(auto &p:floatPublished.vertices) p={double(float(p.x-floatOrigin.x)),double(float(p.y-floatOrigin.y)),double(float(p.z-floatOrigin.z))};
    errors.clear(); auto floatOK=csg::validate(floatPublished,errors);
    if(!floatOK) for(const auto &error:errors) std::cerr<<"float publication: "<<error.message<<'\n';
    require(!floatOK,"unrepresentable sub-float slivers must be rejected");
    room=beforeRepeats; repeated=room.root.children.back();
    for(int i=0;i<8;++i)
    {
      auto &p=repeated.transform.column[3]; p=p+csg::Vec{0,0.2,0.3};
      p={std::round(p.x/0.01)*0.01,std::round(p.y/0.01)*0.01,std::round(p.z/0.01)*0.01};
      auto copy=repeated; room.assignIds(copy); room.root.children.push_back(copy);
    }
    auto snappedResult=roomEvaluator.evaluate(room); require(snappedResult.success,"grid-snapped repeat evaluation");
    errors.clear(); require(csg::triangulateForPublication(*snappedResult.mesh,repeatedPublished,errors),"grid-snapped repeat triangulation");
    floatPublished=repeatedPublished; floatOrigin=floatPublished.vertices.front();
    for(auto &p:floatPublished.vertices) p={double(float(p.x-floatOrigin.x)),double(float(p.y-floatOrigin.y)),double(float(p.z-floatOrigin.z))};
    errors.clear(); require(csg::validate(floatPublished,errors),"grid-snapped repeat float publication");
    std::cout<<"CSG regression tests passed\n"; return 0;
  }
  catch(const std::exception &e) { std::cerr<<"FAIL: "<<e.what()<<'\n'; return 1; }
}
