#
# setup python environment variables
#

# find out the root directory of the environment.sh
filePath=$BASH_SOURCE
fullPath=$(readlink -f $filePath)

# append directory to PythonPath
srcDir=$(dirname $fullPath)
PYTHONPATH=$srcDir:$srcDir/protocol:${PYTHONPATH}
export PYTHONPATH
