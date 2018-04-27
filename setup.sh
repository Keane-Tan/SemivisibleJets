SVJ_top_dir(){
  local Canonicalize="readlink -f"
  $Canonicalize asdf &> /dev/null || Canonicalize=realpath
  dirname "$($Canonicalize "${BASH_SOURCE[0]}")"
}

SVJ_cvmfs_PythonDir=/cvmfs/sft.cern.ch/lcg/releases/Python/2.7.13-597a5/x86_64-slc6-gcc62-opt/
SVJ_cvmfs_PipDir=/cvmfs/sft.cern.ch/lcg/releases/pip/8.1.2-c9f5a/x86_64-slc6-gcc62-opt/
SVJ_cvmfs_GCCSetup=/cvmfs/sft.cern.ch/lcg/contrib/gcc/6.2/x86_64-slc6/setup.sh
source "${SVJ_cvmfs_GCCSetup}"

export SVJ_TOP_DIR="$(SVJ_top_dir)"
export MG_GENPROD_DIR="${SVJ_TOP_DIR}/genproductions/bin/MadGraph5_aMCatNLO"
export PYTHONPATH=${PYTHONPATH}:${SVJ_TOP_DIR}/Utils/:${SVJ_cvmfs_PythonDir}/lib/python2.7/site-packages/:${SVJ_cvmfs_PipDir}/lib/python2.7/site-packages/
export PATH=${PATH}:${SVJ_cvmfs_PythonDir}/bin:${SVJ_cvmfs_PipDir}/bin

# Install required Python packages
pip install -r requirements.txt --ignore-installed --user