// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <csg/runtime.h>
#include <exception>
namespace csg
{
RuntimeModel::RuntimeModel() { source.assignIds(source.root); }
bool RuntimeModel::commit(Document candidate,const Publisher &publish,Diagnostics &errors)
{
  if(updating) { errors.push_back({Code::InvalidDocument,0,0,"Reentrant runtime CSG update"}); return false; }
  updating=true; struct Guard { bool &value; ~Guard(){value=false;} } guard{updating};
  auto result=evaluator.evaluate(candidate);
  if(!result.success) { errors.insert(errors.end(),result.diagnostics.begin(),result.diagnostics.end()); return false; }
  result.revision=published.revision+1;
  try {
    if(!publish || !publish(result)) { errors.push_back({Code::InvalidResult,0,0,"Runtime geometry publication rejected"}); return false; }
  } catch(const std::exception &e) {
    errors.push_back({Code::InvalidResult,0,0,e.what()}); return false;
  } catch(...) { errors.push_back({Code::InvalidResult,0,0,"Runtime geometry publication threw an exception"}); return false; }
  source=std::move(candidate); published=std::move(result); return true;
}
}
