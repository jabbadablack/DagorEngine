// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <libTools/CSG/brush.h>
#include <csg/runtime.h>
#include <cmath>
#include <iostream>
#include <map>
#include <stdexcept>
#include <cstring>

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
    auto pinched=*touching.mesh;
    bool joinedPoint=false;
    for(size_t i=0;i<pinched.vertices.size() && !joinedPoint;++i)
      for(size_t j=i+1;j<pinched.vertices.size();++j)
        if(pinched.vertices[i].x==pinched.vertices[j].x && pinched.vertices[i].y==pinched.vertices[j].y &&
          pinched.vertices[i].z==pinched.vertices[j].z) {
          for(auto &face:pinched.faces) for(auto &index:face.vertices) if(index==j) index=uint32_t(i);
          joinedPoint=true; break;
        }
    errors.clear(); require(joinedPoint && !csg::validate(pinched,errors),"reject closed shells sharing a single vertex index");
    errors.clear(); require(csg::validate(*touching.mesh,errors),"separate point-contact shells remain valid");
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
    csg::Extrusion shape; shape.polygon={{0,0,0},{2,0,0},{2,1,0},{1,1,0},{1,2,0},{0,2,0}};
    shape.depth=2; csg::Mesh generated;
    errors.clear(); require(csg::generateExtrusion(shape,generated,errors),"parametric concave depth");
    near(csg::volume(generated),6,"parametric depth volume");
    shape.mode=csg::ExtrusionMode::Spin; shape.polygon={{1,0,0},{2,0,0},{2,2,0},{1,2,0}};
    shape.spinSides=32; errors.clear();
    bool generatedOK=csg::generateExtrusion(shape,generated,errors);
    if(!generatedOK) for(auto &e:errors) std::cerr<<e.message<<'\n';
    require(generatedOK,"closed spin with hole");
    near(csg::volume(generated),32*std::sin(2*3.141592653589793/32)*3,"spin discrete volume");
    shape.spinDegrees=180; errors.clear(); require(csg::generateExtrusion(shape,generated,errors),"partial spin capped");
    shape.spinDegrees=360; shape.polygon={{0,0,0},{2,0,0},{2,2,0},{0,2,0}};
    errors.clear(); require(csg::generateExtrusion(shape,generated,errors),"spin touching axis");
    shape.mode=csg::ExtrusionMode::Path; shape.polygon={{-0.1,-0.1,0},{0.1,-0.1,0},{0.1,0.1,0},{-0.1,0.1,0}};
    shape.path={{{0,0,0},{},{0,0,-1}},{{0,0,-4},{0,0,1},{}}};
    errors.clear(); require(csg::generateExtrusion(shape,generated,errors),"straight Bezier sweep");
    near(csg::volume(generated),0.16,"straight sweep volume");
    shape.path[1].position={2,1,-4}; shape.path[1].incoming={-1,0,0}; shape.path[1].tilt=0.3;
    errors.clear(); generatedOK=csg::generateExtrusion(shape,generated,errors);
    if(!generatedOK) for(auto &e:errors) std::cerr<<e.message<<'\n';
    require(generatedOK,"curved tilted Bezier sweep");
    auto sharedUv=[&](const csg::Mesh &mesh) {
      for(size_t i=0;i<mesh.faces.size();++i) for(size_t j=i+1;j<mesh.faces.size();++j) {
        const auto &a=mesh.faces[i],&b=mesh.faces[j];
        if(a.id!=b.id) continue;
        unsigned common=0; for(auto x:a.vertices) for(auto y:b.vertices) if(x==y) ++common;
        if(common!=2) continue;
        for(auto x:a.vertices) for(auto y:b.vertices) if(x==y) {
          auto u=csg::textureCoordinates(a.surface,mesh.vertices[x]),v=csg::textureCoordinates(b.surface,mesh.vertices[y]);
          require(std::abs(u[0]-v[0])<1e-7 && std::abs(u[1]-v[1])<1e-7,"continuous sweep UV across triangulation");
        }
      }
    }; sharedUv(generated);
    shape.pathJoined=true; double handle=4*0.5522847498307936;
    shape.path={{{4,0,0},{0,0,handle},{0,0,-handle}},{{0,0,-4},{handle,0,0},{-handle,0,0}},
      {{-4,0,0},{0,0,-handle},{0,0,handle}},{{0,0,4},{-handle,0,0},{handle,0,0}}};
    errors.clear(); generatedOK=csg::generateExtrusion(shape,generated,errors);
    if(!generatedOK) for(auto &e:errors) std::cerr<<e.message<<'\n';
    require(generatedOK,"closed Bezier sweep seam");
    csg::Document paramDoc; paramDoc.assignIds(paramDoc.root);
    csg::Node sweepOuter; sweepOuter.brush=csg::box({12,4,12}); paramDoc.assignIds(sweepOuter); paramDoc.root.children.push_back(sweepOuter);
    csg::Node sweep; sweep.parametric=true; sweep.extrusion=shape; sweep.operation=csg::Operation::Subtract;
    paramDoc.assignIds(sweep); paramDoc.root.children.push_back(sweep);
    csg::Evaluator paramEval; auto cutSweep=paramEval.evaluate(paramDoc);
    if(!cutSweep.success) for(auto &e:cutSweep.diagnostics) std::cerr<<e.message<<'\n';
    require(cutSweep.success,"runtime boolean subtraction of closed path extrusion");
    near(csg::volume(*cutSweep.mesh),576-csg::volume(generated),"swept tunnel cut volume");
    auto reused=paramEval.evaluate(paramDoc); require(reused.success && reused.cacheHits==1,"parametric result cached");
    paramDoc.root.children[1].extrusion.path[0].position.x+=0.1;
    auto paramEdit=paramEval.evaluate(paramDoc); csg::Evaluator paramFull; auto paramRebuilt=paramFull.evaluate(paramDoc);
    require(paramEdit.success && paramRebuilt.success,"editable path reevaluation");
    near(csg::volume(*paramEdit.mesh),csg::volume(*paramRebuilt.mesh),"parametric incremental/full equivalence");
    shape.pathJoined=false; shape.path={{{0,0,0},{},{0,0,-1}},{{2,1,-4},{-1,0,0},{}}};
    errors.clear(); require(csg::generateExtrusion(shape,generated,errors),"restore curved sweep");
    auto preserved=generated;
    shape.path[1].position=shape.path[0].position;
    errors.clear(); require(!csg::generateExtrusion(shape,generated,errors),"reject collapsed sweep");
    near(csg::volume(generated),csg::volume(preserved),"failed sweep is transactional");
    shape.mode=csg::ExtrusionMode::Depth; shape.polygon={{0,0,0},{2,2,0},{0,2,0},{2,0,0}};
    errors.clear(); require(!csg::generateExtrusion(shape,generated,errors),"reject crossed parametric profile");
    shape.polygon={{0,0,0},{0,2,0},{2,2,0},{2,0,0}};
    errors.clear(); require(csg::generateExtrusion(shape,generated,errors),"clockwise depth profile");
    shape.mode=csg::ExtrusionMode::Spin;
    errors.clear(); require(csg::generateExtrusion(shape,generated,errors),"clockwise spin profile");
    csg::Extrusion foldedOffset; foldedOffset.mode=csg::ExtrusionMode::Path;
    foldedOffset.polygon={{1,-0.2,0},{1.4,-0.2,0},{1.4,0.2,0},{1,0.2,0}};
    foldedOffset.path={{{0,0,0},{},{0,0,-0.5}},{{0.5,0,-2},{0,0,0.5},{}}};
    errors.clear(); require(!csg::generateExtrusion(foldedOffset,generated,errors) && !errors.empty(),
      "reject offset profile folding through the inside of a tight Bezier bend");
    csg::Extrusion mappedExtrusion; mappedExtrusion.polygon={{0,0,0},{2,0,0},{2,2,0},{0,2,0}};
    mappedExtrusion.surfaces.resize(6,{mappedExtrusion.surface,true});
    mappedExtrusion.surfaces[2].surface.material="per-edge material";
    mappedExtrusion.surfaces[2].surface.scaleU=2; mappedExtrusion.surfaces[2].surface.offsetV=0.25;
    mappedExtrusion.surfaces[2].surface.smoothing=8;
    errors.clear(); require(csg::generateExtrusion(mappedExtrusion,generated,errors),"per-surface extrusion mapping");
    for(const auto &face:generated.faces) {
      require((face.surface.material=="per-edge material")== (face.id==3),"extrusion material stays on its logical surface");
      if(face.id==3) require(face.surface.smoothing==8,"extrusion preserves explicit smoothing");
    }
    mappedExtrusion.surfaces[2].automaticUv=false;
    mappedExtrusion.surfaces[2].surface.u={0,0,1}; mappedExtrusion.surfaces[2].surface.v={1,0,0};
    errors.clear(); require(csg::generateExtrusion(mappedExtrusion,generated,errors),"explicit extrusion mapping axes");
    for(const auto &face:generated.faces) if(face.id==3) for(auto index:face.vertices) {
      auto actual=csg::textureCoordinates(face.surface,generated.vertices[index]);
      auto expected=csg::textureCoordinates(mappedExtrusion.surfaces[2].surface,generated.vertices[index]);
      near(actual[0],expected[0],"aligned extrusion U is not overwritten");
      near(actual[1],expected[1],"aligned extrusion V is not overwritten");
    }
    mappedExtrusion.surfaces.pop_back(); errors.clear();
    require(!csg::generateExtrusion(mappedExtrusion,generated,errors),"reject mismatched extrusion surface slots");
    csg::RuntimeModel runtime; auto candidate=runtime.document();
    csg::Node runtimeSolid; runtimeSolid.brush=csg::box({4,4,4}); candidate.assignIds(runtimeSolid); candidate.root.children.push_back(runtimeSolid);
    unsigned publications=0;
    auto publish=[&](const csg::Result &result) { require(result.success && bool(result.mesh),"runtime receives immutable geometry"); ++publications; return true; };
    errors.clear(); require(runtime.commit(candidate,publish,errors),"runtime initial publication");
    near(csg::volume(*runtime.result().mesh),64,"runtime initial volume");
    auto originalRuntime=runtime.result().mesh;
    candidate=runtime.document(); csg::Node runtimeCut; runtimeCut.parametric=true; runtimeCut.extrusion=shape;
    runtimeCut.operation=csg::Operation::Subtract; candidate.assignIds(runtimeCut); candidate.root.children.push_back(runtimeCut);
    errors.clear(); require(!runtime.commit(candidate,publish,errors),"reject non-manifold tangential cut");
    require(runtime.result().mesh==originalRuntime && publications==1,"non-manifold cut leaves publication unchanged");
    candidate.root.children.back().extrusion.polygon={{0,-0.5,0},{0,0.5,0},{0.75,0.5,0},{0.75,-0.5,0}};
    auto reject=[](const csg::Result &) { return false; };
    errors.clear(); require(!runtime.commit(candidate,reject,errors),"runtime publication rejection");
    require(runtime.result().mesh==originalRuntime && runtime.result().revision==1,"runtime publication failure retains revision");
    errors.clear(); bool runtimeOK=runtime.commit(candidate,publish,errors);
    if(!runtimeOK) for(auto &e:errors) std::cerr<<"runtime: "<<e.message<<'\n';
    require(runtimeOK,"runtime accepts cut after failed publication");
    require(runtime.result().revision==2 && publications==2,"runtime revisions advance only on publication");
    near(csg::volume(*originalRuntime),64,"prior runtime geometry remains immutable after cutting");
    auto lastRuntime=runtime.result().mesh; candidate=runtime.document(); candidate.root.children.back().extrusion.spinDegrees=std::nan("");
    errors.clear(); require(!runtime.commit(candidate,publish,errors),"runtime invalid cut rejected before publication");
    require(runtime.result().mesh==lastRuntime && publications==2,"runtime invalid cut preserves render/collision revision");
    auto spinRoom=beforeRepeats;
    spinRoom.root.children.pop_back(); // Match the UI fixture: no extra floor-crossing box.
    csg::Node roomSpin; roomSpin.parametric=true; roomSpin.extrusion.mode=csg::ExtrusionMode::Spin;
    roomSpin.extrusion.polygon={{0,0,0},{2,0,0},{2,2,0},{0,2,0}};
    spinRoom.assignIds(roomSpin); spinRoom.root.children.push_back(roomSpin);
    csg::Evaluator spinRoomEval; auto spinRoomResult=spinRoomEval.evaluate(spinRoom);
    require(spinRoomResult.success,"spin crossing room floor evaluates");
    csg::Mesh spinPublished; csg::Vec spinOrigin;
    errors.clear(); bool spinPublication=csg::prepareFloatPublication(*spinRoomResult.mesh,spinPublished,spinOrigin,errors);
    if(!spinPublication) for(auto &e:errors) std::cerr<<"spin publication: "<<e.message<<'\n';
    require(spinPublication,"spin crossing room floor survives float triangulation");
    auto torusRoom=beforeRepeats; torusRoom.root.children.pop_back();
    csg::Node roomTorus; roomTorus.parametric=true; roomTorus.extrusion.mode=csg::ExtrusionMode::Spin; roomTorus.extrusion.spinSides=16;
    for(int i=0;i<16;++i) { double angle=2*3.14159265358979323846*i/16;
      roomTorus.extrusion.polygon.push_back({2+0.5*std::cos(angle),0.5*std::sin(angle),0}); }
    torusRoom.assignIds(roomTorus); torusRoom.root.children.push_back(roomTorus);
    csg::Evaluator torusRoomEval; auto torusRoomResult=torusRoomEval.evaluate(torusRoom);
    if(!torusRoomResult.success) for(auto &e:torusRoomResult.diagnostics) std::cerr<<"torus room: "<<e.message<<'\n';
    require(torusRoomResult.success,"torus crossing room floor evaluates");
    csg::Mesh torusPublished; csg::Vec torusOrigin; errors.clear();
    require(csg::prepareFloatPublication(*torusRoomResult.mesh,torusPublished,torusOrigin,errors),"torus crossing room floor publishes");
    require(std::abs(csg::volume(torusPublished)-csg::volume(*torusRoomResult.mesh))<
      csg::volume(*torusRoomResult.mesh)*1e-6,"torus float publication preserves volume within float precision");
    csg::Document chunkDoc; chunkDoc.assignIds(chunkDoc.root);
    for(int i=0;i<2;++i) { csg::Node node; node.brush=csg::box({1,1,1}); node.transform.column[3].x=i*4; chunkDoc.assignIds(node); chunkDoc.root.children.push_back(node); }
    csg::Evaluator chunkEvaluator; auto chunkFirst=chunkEvaluator.evaluate(chunkDoc);
    require(chunkFirst.success && chunkFirst.chunks.size()==2,"disjoint cache chunks exposed");
    auto chunkCached=chunkEvaluator.evaluate(chunkDoc);
    require(chunkCached.chunks.size()==2 && chunkCached.chunks[0].mesh==chunkFirst.chunks[0].mesh,"cached root retains disjoint chunks");
    chunkDoc.root.visible=false; auto chunkHidden=chunkEvaluator.evaluate(chunkDoc);
    require(chunkHidden.success && chunkHidden.mesh->faces.empty(),"hidden root publishes empty output");
    chunkDoc.root.visible=true; auto chunkShown=chunkEvaluator.evaluate(chunkDoc);
    require(chunkShown.success && chunkShown.chunks.size()==2 && chunkShown.chunks[0].mesh==chunkFirst.chunks[0].mesh,
      "cached chunks survive an intervening hidden root revision");
    chunkDoc.root.children[1].transform.column[3].x+=0.25; auto chunkEdited=chunkEvaluator.evaluate(chunkDoc);
    require(chunkEdited.success && chunkEdited.chunks.size()==2 && chunkEdited.chunks[0].mesh==chunkFirst.chunks[0].mesh &&
      chunkEdited.chunks[0].hash==chunkFirst.chunks[0].hash && chunkEdited.chunks[1].hash!=chunkFirst.chunks[1].hash,"unaffected published chunk reused");
    near(csg::volume(*chunkEdited.mesh),csg::volume(*chunkEdited.chunks[0].mesh)+csg::volume(*chunkEdited.chunks[1].mesh),"chunk geometry equals complete geometry");
    errors.clear(); require(csg::validateClosedMesh(*touching.mesh,errors),"closed mesh validation preserves separate point-contact components");
    require(!csg::booleanOperation(a,b,csg::Operation(3)).success,"unknown runtime boolean operation must be rejected");
    auto invalidOperation=chunkDoc; invalidOperation.root.operation=csg::Operation(3);
    require(!chunkEvaluator.evaluate(invalidOperation).success,"unknown document operation must be rejected");
    csg::Document nonfiniteGroup; nonfiniteGroup.assignIds(nonfiniteGroup.root);
    // Inject serialized IEEE bits rather than constructing NaN with floating-point
    // operations in a consumer that may be compiled with the game's fast-math flags.
    volatile uint64_t invalidTransformBits=UINT64_C(0x7ff8000000000000);
    const uint64_t invalidTransformCopy=invalidTransformBits;
    std::memcpy(&nonfiniteGroup.root.transform.column[3].x,&invalidTransformCopy,sizeof(invalidTransformCopy));
    require(!csg::finite(nonfiniteGroup.root.transform.column[3]),"non-finite test input reaches the precise API");
    require(!chunkEvaluator.evaluate(nonfiniteGroup).success,"non-finite empty group transform must be rejected");
    csg::Node heldAggregate; heldAggregate.brush=*chunkFirst.mesh;
    const auto heldHash=csg::fingerprint(heldAggregate);
    for(unsigned edit=0;edit<6;++edit) {
      chunkDoc.root.children.back().transform.column[3].y=edit*0.1;
      require(chunkEvaluator.evaluate(chunkDoc).success,"aggregate buffer reuse evaluates");
      heldAggregate.brush=*chunkFirst.mesh;
      require(csg::fingerprint(heldAggregate)==heldHash,"retained aggregate snapshots remain immutable");
    }
    std::cout<<"CSG regression tests passed\n"; return 0;
  }
  catch(const std::exception &e) { std::cerr<<"FAIL: "<<e.what()<<'\n'; return 1; }
}
