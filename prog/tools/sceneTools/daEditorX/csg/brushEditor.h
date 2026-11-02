// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
#include "brushDocument.h"
#include <functional>
#include <map>
#include <EditorCore/ec_rendEdObject.h>

class ObjEd;
class GeomObject;
class StaticGeometryContainer;
class IGenViewportWnd;
class MaterialData;
class ITextureNumerator;
class BrushEditor
{
public:
  explicit BrushEditor(ObjEd &owner);
  ~BrushEditor();
  void show() { visible=true; }
  bool isVisible() const { return visible; }
  void reset();
  void save(DataBlock &block);
  void load(const DataBlock &block);
  void update();
  void render();
  void renderTrans();
  void renderHandles();
  bool pick(IGenViewportWnd *viewport,int x,int y,bool toggle);
  bool validForExport();
  void gather(StaticGeometryContainer &container,bool collision);
  void updateImgui();
  void restore(csg::Document value);
  std::pair<int,float> mappingSettings() const { return {lightmapSize,lightmapSampleSize}; }
  void restoreMappingSettings(std::pair<int,float> value) { lightmapSize=value.first; lightmapSampleSize=value.second; dirty=true; }
  csg::Document document;
  bool collectRuntimeTextures(ITextureNumerator &textures);
  bool writeRuntimeSettings(DataBlock &source,const ITextureNumerator &textures);
  void syncGizmo();
  void transformSelection(const TMatrix &before,const TMatrix &after);
  void putTransformUndo();
  bool selectionBounds(BBox3 &box) const;
  void activateSelection();
  bool deleteSelection();
  bool duplicateSelection();
private:
  MaterialData *resolveMaterial(const std::string &name,csg::Id brush=0,csg::Id face=0);
  std::map<std::string,Ptr<MaterialData>> runtimePalette();
  ObjEd &owner;
  csg::Evaluator evaluator;
  csg::Result current;
  csg::Id selected = 0;
  csg::Id pendingMove = 0, pendingParent = 0;
  std::vector<uint32_t> components;
  int mode = 0, faceIndex = 0;
  bool dirty = true, loadFailed = false, visible = false;
  DataBlock *unreadDocument = nullptr;
  GeomObject *preview = nullptr;
  struct PublishedPart { GeomObject *geometry=nullptr; std::shared_ptr<StaticGeometryContainer> container; std::shared_ptr<void> physics; };
  std::map<uint64_t,PublishedPart> parts;
  StaticGeometryContainer *published = nullptr;
  double updateMs = 0;
  std::unique_ptr<csg::Document> benchmarkSource;
  int benchmarkFrame = -1;
  int benchmarkNeighbors = 0;
  csg::Id benchmarkEdited = 0;
  double benchmarkWorst = 0;
  void startBenchmark();
  bool acceptanceQueued = false;
  bool benchmarkQueued = false;
  void runAcceptance();
  double grid = 0.01, angleSnap = 15, distance = 1;
  int repeatCount = 8, cylinderSides = 16;
  float size[3] = {2,2,2}, increment[3] = {0,0.2f,0.3f}, repeatRotation[3] = {}, repeatScale[3] = {1,1,1};
  float clipNormal[3] = {1,0,0}, clipDistance = 0;
  char outline[4096] = "0 0 0\n2 0 0\n2 0 1\n1 0 1\n1 0 2\n0 0 2";
  float extrusion[3] = {0,2,0};
  char replaceFrom[256] = {}, replaceTo[256] = {};
  csg::Surface copiedSurface;
  Ptr<RenderableEditableObject> gizmo;
  bool haveCopiedSurface = false;
  int lightmapSize = 1024;
  float lightmapSampleSize = 0.1f;
  std::string defaultTexture;
  std::string defaultNormalTexture;
  csg::Diagnostics editErrors;
  void edit(const char *label,const std::function<bool()> &action);
  void hierarchy(csg::Node &node);
  void add(csg::Mesh mesh,const char *name);
  void addExtrusion(csg::Extrusion source,const char *name);
  void addNativeGeometry(const StaticGeometryContainer &source,const char *name,bool preserve_smoothing=false);
  void importClosedMesh();
  void modelling(csg::Node &node);
  void extrusionProperties(csg::Node &node);
  csg::Id extrusionEditing = 0;
  uint64_t extrusionFingerprint = 0;
  csg::Extrusion extrusionDraft;
  std::vector<csg::Id> extrusionDraftSurfaces;
  int extrusionProfilePoint = 0, extrusionCurvePoint = 0;
  void surfaces(csg::Node &node);
  void drawContents();
  bool buildPublished(const csg::Mesh &mesh,StaticGeometryContainer &container);
};
