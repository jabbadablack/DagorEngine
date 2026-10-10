# Animation state graph (ASG) data for tools: states, nodes, the anim tree, conditions, loading and export
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(sources
  asg_data.cpp
  asg_export.cpp
  asg_scheme.cpp
  asg_nodes.cpp
  asg_cond_parser.cpp
  asg_anim_load.cpp
  asg_anim_save.cpp
  asg_anim_tree.cpp
)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
