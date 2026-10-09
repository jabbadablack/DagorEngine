# detect linux/macOS host and build path to proper tools in DAGOR_CDK_DIR; source it: . make_dagor_tools_path.sh
_dagor_jbuild_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
case "$(uname -s)" in
  Darwin) DAGOR_CDK_DIR="$_dagor_jbuild_dir/../../tools/dagor_cdk/macOS-x86_64" ;;
  *)      DAGOR_CDK_DIR="$_dagor_jbuild_dir/../../tools/dagor_cdk/linux-$(uname -m)" ;;
esac
export DAGOR_CDK_DIR
unset _dagor_jbuild_dir
